"""Fixed-origin HTTPS client; only the OAuth slice's routes are active."""

import json
import socket
import threading
from typing import Any, cast

import requests
from pydantic import ValidationError
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPSConnection
from urllib3.connectionpool import HTTPSConnectionPool

from .schemas import DomainError, SellerProfile


class DeadlineHTTPSConnection(HTTPSConnection):
    """Interrupt a connected socket, including slow headers/body, after 45s.

    The OS DNS resolver is not cancellable here; this is NOT a hard wall-clock
    guarantee for name resolution. Never retry a failed POST to compensate.
    """

    REQUEST_BUDGET_SECONDS = 45.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._deadline_lock = threading.Lock()
        self._deadline_timer = None
        self._deadline_expired = False
        self._request_socket = None

    def disarm_deadline(self):
        with self._deadline_lock:
            timer, self._deadline_timer = self._deadline_timer, None
            self._request_socket = None
        if timer:
            timer.cancel()

    def request(self, *args, **kwargs):
        self.disarm_deadline()

        def expire():
            with self._deadline_lock:
                if self._deadline_timer is not timer:
                    return
                self._deadline_expired = True
                connection = self.sock or self._request_socket
            if connection is not None:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

        with self._deadline_lock:
            self._deadline_expired = False
            self._request_socket = self.sock
            timer = threading.Timer(self.REQUEST_BUDGET_SECONDS, expire)
            timer.daemon = True
            self._deadline_timer = timer
        timer.start()
        try:
            super().request(*args, **kwargs)
            if self._deadline_expired:
                raise TimeoutError("HTTPS request budget exhausted")
        except BaseException:
            self.disarm_deadline()
            self.close()
            raise

    def connect(self):
        super().connect()
        self._request_socket = self.sock
        if self._deadline_expired:
            self.close()
            raise TimeoutError("HTTPS request budget exhausted during connection")

    def close(self):
        # HTTP/1.0 or Connection: close detaches the socket at header receipt,
        # while the response's makefile still reads its body. Keep the watchdog
        # attached to that socket until the caller closes/consumes the response.
        super().close()

    def getresponse(self):
        response = super().getresponse()
        setattr(response, "_oauth_deadline_connection", self)
        return response


class DeadlineHTTPSPool(HTTPSConnectionPool):
    # urllib3's structural connection protocol rejects its own ClassVar shape
    # under some checkers; runtime inheritance matches the pinned 2.8.0 API.
    ConnectionCls = cast(Any, DeadlineHTTPSConnection)

    def _put_conn(self, conn):
        if isinstance(conn, DeadlineHTTPSConnection):
            conn.disarm_deadline()
        super()._put_conn(conn)


class DeadlineAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        super().init_poolmanager(*args, **kwargs)
        # Instance-local copy: do not change urllib3's global pool registry.
        self.poolmanager.pool_classes_by_scheme = {
            **self.poolmanager.pool_classes_by_scheme, "https": DeadlineHTTPSPool,
        }


class MercadoLivreClient:
    """Serialize access in AuthManager; never retry a one-use OAuth POST."""

    BASE = "https://api.mercadolibre.com"

    def __init__(self, *, connect_timeout: float = 5, read_timeout: float = 30):
        if not 0 < connect_timeout <= 30 or not 0 < read_timeout <= 60:
            raise DomainError("CONFIGURATION_ERROR", "Timeout HTTP fora da faixa permitida.")
        self.timeout = (connect_timeout, read_timeout)
        self.lock = threading.RLock()
        self.session = requests.Session()
        self.session.mount("https://", DeadlineAdapter(max_retries=0))
        self.session.trust_env = False  # No ambient proxy, netrc or CA overrides.
        self.session.headers.update({"Accept": "application/json"})

    def close(self):
        with self.lock:
            self.session.close()

    def _request(self, method: str, path: str, *, token=None, form=None) -> dict:
        if (method, path) not in {("GET", "/users/me"), ("POST", "/oauth/token")}:
            raise DomainError("PERMISSION_DENIED", "Metodo ou rota fora da allowlist OAuth.")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = None
        try:
            with self.lock, self.session.request(
                method, self.BASE + path, headers=headers, data=form,
                timeout=self.timeout, allow_redirects=False, verify=True, stream=True,
            ) as response:
                if response.status_code != 200:
                    if response.status_code == 401:
                        code = "AUTH_REQUIRED"
                    elif response.status_code == 403:
                        code = "PERMISSION_DENIED"
                    elif response.status_code == 429:
                        code = "RATE_LIMITED"
                    else:
                        code = "OAUTH_REJECTED" if method == "POST" else "API_UNAVAILABLE"
                    raise DomainError(code, f"API retornou HTTP {response.status_code}; nenhum payload foi registrado.")
                if "application/json" not in response.headers.get("Content-Type", "").lower():
                    raise DomainError("INVALID_API_RESPONSE", "Resposta da API nao e JSON.")
                body = bytearray()
                for chunk in response.iter_content(8192):
                    body.extend(chunk)
                    if len(body) > 1024 * 1024:
                        raise DomainError("INVALID_API_RESPONSE", "Resposta excedeu o limite local.")
                result = json.loads(body)
                if not isinstance(result, dict):
                    raise ValueError("not an object")
                return result
        except requests.RequestException:
            code = "OAUTH_RESULT_UNCERTAIN" if method == "POST" else "API_UNAVAILABLE"
            raise DomainError(code, "Falha de transporte; POST OAuth nao sera repetido automaticamente.") from None
        except (ValueError, UnicodeError):
            code = "OAUTH_RESULT_UNCERTAIN" if method == "POST" else "INVALID_API_RESPONSE"
            raise DomainError(code, "Resposta invalida; nao reapresentar credencial de uso unico.") from None
        finally:
            if response is not None:
                connection = getattr(response.raw, "_oauth_deadline_connection", None)
                if isinstance(connection, DeadlineHTTPSConnection):
                    connection.disarm_deadline()

    def exchange(self, form: dict) -> dict:
        return self._request("POST", "/oauth/token", form=form)

    def profile(self, access_token: str) -> SellerProfile:
        raw = self._request("GET", "/users/me", token=access_token)
        try:
            identity = raw.get("id")
            if isinstance(identity, bool) or not isinstance(identity, (str, int)):
                raise ValueError("missing id")
            return SellerProfile(
                seller_id=str(identity), nickname=raw["nickname"],
                country_id=raw.get("country_id"), site_id=raw.get("site_id"),
            )
        except (KeyError, ValueError, ValidationError):
            raise DomainError("INVALID_API_RESPONSE", "Identidade retornada pela API e invalida.") from None
