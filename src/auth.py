"""Local HTTPS OAuth/PKCE, Windows vault and serialized token rotation.

Administrative CLI for the authorized OAuth slice, not an extra MCP tool.
No network, vault access or listener is started at import time.
"""

import argparse
import base64
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import secrets
import ssl
import sys
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit
import webbrowser

from dotenv import load_dotenv
from pydantic import SecretStr, ValidationError

from .client import MercadoLivreClient
from .schemas import DomainError, TokenRecord, success

ROOT = Path(__file__).resolve().parent.parent
REDIRECT_URI = "https://127.0.0.1:8000/callback"
AUTHORIZATION_ENDPOINT = "https://auth.mercadolivre.com.br/authorization"


def local_directory() -> Path:
    if os.name != "nt" or not os.environ.get("LOCALAPPDATA"):
        raise DomainError("CONFIGURATION_ERROR", "Este recorte requer Windows e LOCALAPPDATA.")
    return Path(os.environ["LOCALAPPDATA"]) / "DiasMoto" / "mercadolivre-mcp"


@dataclass(frozen=True)
class AuthConfig:
    client_id: str
    client_secret: SecretStr = field(repr=False)
    cert_file: Path
    key_file: Path = field(repr=False)
    credential_profile: str = "default"
    redirect_uri: str = REDIRECT_URI

    def __post_init__(self):
        if not re.fullmatch(r"[0-9]+", self.client_id):
            raise DomainError("CONFIGURATION_ERROR", "ML_CLIENT_ID deve conter somente digitos.")
        if not self.client_secret.get_secret_value().strip():
            raise DomainError("CONFIGURATION_ERROR", "ML_CLIENT_SECRET ausente.")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", self.credential_profile):
            raise DomainError("CONFIGURATION_ERROR", "ML_CREDENTIAL_PROFILE invalido.")
        if self.redirect_uri != REDIRECT_URI:
            raise DomainError("CONFIGURATION_ERROR", "ML_REDIRECT_URI deve ser https://127.0.0.1:8000/callback.")

    @classmethod
    def load(cls):
        # The user populates this file locally. Values never enter diagnostics.
        load_dotenv(ROOT / ".env", override=False)

        def credential(primary, legacy):
            value, old = os.environ.get(primary), os.environ.get(legacy)
            if value and old and value != old:
                raise DomainError("CONFIGURATION_ERROR", f"Conflito entre {primary} e {legacy}; mantenha um valor local.")
            value = value or old
            if not value:
                raise DomainError("CONFIGURATION_ERROR", f"Variavel ausente: {primary}.")
            return value

        # Explicit compatibility with the user's preexisting CLIENT_ID/CLIENT_SECRET.
        client_id = credential("ML_CLIENT_ID", "CLIENT_ID")
        secret = credential("ML_CLIENT_SECRET", "CLIENT_SECRET")
        if os.environ.get("ML_PKCE_ENABLED", "true").lower() != "true":
            raise DomainError("CONFIGURATION_ERROR", "Este recorte exige PKCE S256; habilite-o no portal.")
        tls = local_directory() / "tls"
        return cls(
            client_id=client_id, client_secret=SecretStr(secret),
            cert_file=Path(os.environ.get("ML_CALLBACK_CERT_FILE") or tls / "callback.pem"),
            key_file=Path(os.environ.get("ML_CALLBACK_KEY_FILE") or tls / "callback-key.pem"),
            credential_profile=os.environ.get("ML_CREDENTIAL_PROFILE", "default"),
            redirect_uri=os.environ.get("ML_REDIRECT_URI", REDIRECT_URI),
        )

    def tls_context(self):
        if not self.cert_file.is_absolute() or not self.key_file.is_absolute():
            raise DomainError("CONFIGURATION_ERROR", "Caminhos TLS devem ser absolutos.")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        try:
            context.load_cert_chain(str(self.cert_file), str(self.key_file))
        except (OSError, ssl.SSLError):
            raise DomainError("CONFIGURATION_ERROR", "Certificado/chave TLS ausentes ou invalidos.") from None
        return context


class ProfileLock:
    """A held Windows byte-range lock; lock files contain no credentials."""

    def __init__(self, config: AuthConfig):
        import msvcrt
        self.handle = None
        folder = local_directory() / "runtime"
        folder.mkdir(parents=True, exist_ok=True)
        identity = f"{config.client_id}:{config.credential_profile}".encode()
        self.path = folder / (hashlib.sha256(identity).hexdigest() + ".lock")
        handle = self.path.open("a+b")
        try:
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            handle.close()
            raise DomainError("PROCESS_ALREADY_RUNNING", "Outro processo esta usando este perfil OAuth.") from None
        self.handle = handle

    def close(self):
        if self.handle:
            import msvcrt
            try:
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                self.handle.close()
                self.handle = None


class WindowsVault:
    """Use Windows WinVault directly; reject fallback/chained/plaintext backends."""

    SERVICE = "DiasMoto.mercadolivre-mcp.oauth.v1"

    def __init__(self, config: AuthConfig):
        try:
            from keyring.backends.Windows import WinVaultKeyring
            self.backend = WinVaultKeyring()
            if self.backend.priority <= 0:
                raise RuntimeError("unavailable")
        except Exception:
            raise DomainError("SECURE_STORAGE_UNAVAILABLE", "Cofre nativo do Windows indisponivel.") from None
        self.config = config
        self.account = f"{config.client_id}:{config.credential_profile}"

    def load(self):
        try:
            value = self.backend.get_password(self.SERVICE, self.account)
            record = TokenRecord.model_validate_json(value) if value else None
            if record and record.client_id != self.config.client_id:
                raise ValueError("different application")
            return record
        except Exception:
            raise DomainError("SECURE_STORAGE_UNAVAILABLE", "Nao foi possivel ler/validar o registro do cofre.") from None

    def save(self, record: TokenRecord):
        # SecretStr's normal JSON is redacted: unwrap ONLY at this vault boundary.
        value = record.model_dump(mode="json")
        value["access_token"] = record.access_token.get_secret_value()
        value["refresh_token"] = record.refresh_token.get_secret_value()
        serialized = json.dumps(value, separators=(",", ":"))
        try:
            self.backend.set_password(self.SERVICE, self.account, serialized)
            if self.backend.get_password(self.SERVICE, self.account) != serialized:
                raise RuntimeError("readback mismatch")
        except Exception:
            raise DomainError("SECURE_STORAGE_UNAVAILABLE", "Falha ao persistir/verificar tokens; interrompa e reautorize.") from None


def pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    return verifier, challenge


class CallbackServer(ThreadingHTTPServer):
    tls: ssl.SSLContext
    daemon_threads = True
    allow_reuse_address = False
    request_queue_size = 5

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        try:
            # TLS handshake must not block accept() indefinitely.
            return self.tls.wrap_socket(connection, server_side=True), address
        except Exception:
            connection.close()
            raise

    def handle_error(self, request, client_address):
        pass  # Never print request/callback or a traceback.


class AuthManager:
    """One transaction/process/profile; network and vault operations share an RLock."""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.lock = threading.RLock()
        self.listener_lock = threading.Lock()
        self.process_lock = ProfileLock(config)
        try:
            self.vault = WindowsVault(config)
            self.client = MercadoLivreClient()
        except Exception:
            self.process_lock.close()
            raise
        self.server = None
        self.thread = None
        self.timer = None
        self.done = threading.Event()
        self.status = "idle"
        self.error = None
        self.profile_result = None
        self._state = None
        self._verifier = None
        self._url = None
        self.deadline = 0.0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close_listener(self):
        with self.listener_lock:
            server, thread = self.server, self.thread
            self.server = self.thread = None
        if server:
            if thread and thread.ident is not None:
                server.shutdown()
            server.server_close()
        if thread and thread.ident is not None and thread is not threading.current_thread():
            thread.join(timeout=6)

    def close(self):
        if self.timer:
            self.timer.cancel()
        self.close_listener()
        with self.lock:
            self._state = self._verifier = self._url = None
            self.client.close()
            self.process_lock.close()

    def _start_listener(self, *, diagnostic=False):
        manager = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def send_error(self, code, message=None, explain=None):
                self.reply(code, "Requisicao rejeitada.")

            def reply(self, status, message):
                body = message.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                self.close_connection = True

            def do_GET(self):
                try:
                    if len(self.path) > 4096 or sum(len(k) + len(v) for k, v in self.headers.items()) > 8192:
                        self.reply(414, "Requisicao muito grande.")
                        return
                    if self.headers.get("Host") != "127.0.0.1:8000":
                        self.reply(400, "Host invalido.")
                        return
                    if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
                        self.reply(400, "Corpo nao permitido.")
                        return
                    parts = urlsplit(self.path)
                    if parts.scheme or parts.netloc or parts.path != "/callback" or parts.fragment:
                        self.reply(404, "Rota nao encontrada.")
                        return
                    if diagnostic:
                        self.reply(200 if not parts.query else 400, "HTTPS local pronto; nenhum OAuth executado.")
                        return
                    params = parse_qs(parts.query, keep_blank_values=True, max_num_fields=5)
                    allowed = {"code", "state", "error", "error_description", "error_uri"}
                    if set(params) - allowed or any(len(v) != 1 for v in params.values()):
                        raise ValueError("invalid parameters")
                    status, message = manager.receive_callback({k: v[0] for k, v in params.items()})
                    self.reply(status, message)
                except (ValueError, UnicodeError):
                    self.reply(400, "Parametros invalidos.")

        try:
            tls = self.config.tls_context()
            server = CallbackServer(("127.0.0.1", 8000), Handler)
            server.tls = tls
        except OSError:
            raise DomainError("CONFIGURATION_ERROR", "Nao foi possivel iniciar HTTPS loopback na porta 8000.") from None
        self.server = server
        self.thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
        try:
            self.thread.start()
        except Exception:
            # shutdown() deadlocks if serve_forever() has never started.
            self.server = self.thread = None
            server.server_close()
            raise DomainError("CONFIGURATION_ERROR", "Nao foi possivel iniciar a thread do callback.") from None

    def _expire(self):
        with self.lock:
            if self.status != "pending":
                return
            self.status = "expired"
            self.error = DomainError("AUTH_REQUIRED", "Autorizacao expirou; inicie uma nova transacao.")
            self._state = self._verifier = self._url = None
            self.done.set()
        self.close_listener()

    def start_oauth(self, open_browser=True, *, reauthorize=False):
        with self.lock:
            if self.status == "pending":
                return {"status": "pending", "authorization_url": self._url}
            if self.server:
                raise DomainError("CONFIGURATION_ERROR", "Listener ja ativo neste processo.")
            record = self.vault.load()
            if record and record.state == "active" and not reauthorize:
                profile = self.get_profile()
                return {"status": "connected", **profile.model_dump()}
            if record and not reauthorize:
                raise DomainError("AUTH_REQUIRED", "Perfil requer reautorizacao administrativa; use a acao reauthorize.")
            self._state = secrets.token_urlsafe(32)
            self._verifier, challenge = pkce_pair()
            self.deadline = time.monotonic() + 300
            self.done.clear()
            self.error = None
            self.status = "pending"
            self._url = AUTHORIZATION_ENDPOINT + "?" + urlencode({
                "response_type": "code", "client_id": self.config.client_id,
                "redirect_uri": self.config.redirect_uri, "state": self._state,
                "code_challenge": challenge, "code_challenge_method": "S256",
            })
            try:
                self._start_listener()
            except Exception:
                self.status = "failed"
                self._state = self._verifier = self._url = None
                raise
            self.timer = threading.Timer(300, self._expire)
            self.timer.daemon = True
            self.timer.start()
            url = self._url
        if open_browser:
            try:
                webbrowser.open(url, new=1)
            except Exception:
                pass  # Caller may use the official URL, never log it.
        return {"status": "pending", "authorization_url": url}

    def _tokens(self, raw, *, expected_seller=None):
        try:
            lifetime = raw["expires_in"]
            if isinstance(lifetime, bool) or not isinstance(lifetime, (int, float)) or not math.isfinite(lifetime) or lifetime <= 0:
                raise ValueError("invalid expiry")
            user_id = raw["user_id"]
            if isinstance(user_id, bool) or not isinstance(user_id, (str, int)):
                raise ValueError("invalid identity")
            record = TokenRecord(
                client_id=self.config.client_id, seller_id=str(user_id),
                access_token=raw["access_token"], refresh_token=raw["refresh_token"],
                expires_at=time.time() + lifetime,
            )
            if str(raw.get("token_type", "")).lower() != "bearer":
                raise ValueError("invalid token type")
            if expected_seller and record.seller_id != expected_seller:
                raise ValueError("different seller")
            return record
        except (KeyError, ValueError, TypeError, ValidationError):
            raise DomainError("OAUTH_RESULT_UNCERTAIN", "Tokens/identidade invalidos; nao repetir codigo ou refresh token.") from None

    def receive_callback(self, params):
        with self.lock:
            if self.status != "pending":
                return 409, "Transacao inexistente ou ja consumida."
            if time.monotonic() >= self.deadline:
                self._expire()
                return 400, "Autorizacao expirada."
            state = params.get("state", "")
            if not state or not self._state or not hmac.compare_digest(state.encode(), self._state.encode()):
                return 400, "State invalido; nenhuma troca realizada."
            if (bool(params.get("code")) + bool(params.get("error"))) != 1:
                return 400, "Resposta OAuth invalida."
            self.status = "exchanging"  # Claim once, before network I/O.
            verifier = self._verifier
            self._state = self._verifier = self._url = None
            if self.timer:
                self.timer.cancel()
            try:
                if params.get("error"):
                    self.status = "denied"
                    raise DomainError("AUTH_REQUIRED", "Autorizacao recusada pelo usuario ou provedor.")
                raw = self.client.exchange({
                    "grant_type": "authorization_code", "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret.get_secret_value(),
                    "redirect_uri": self.config.redirect_uri, "code": params["code"],
                    "code_verifier": verifier,
                })
                record = self._tokens(raw)
                profile = self.client.profile(record.access_token.get_secret_value())
                if profile.seller_id != record.seller_id:
                    raise DomainError("PERMISSION_DENIED", "Identidade difere da resposta OAuth.")
                previous = self.vault.load()
                if previous and previous.seller_id != record.seller_id:
                    raise DomainError("PERMISSION_DENIED", "Troca de conta exige outro perfil local explicito.")
                self.vault.save(record)
                self.profile_result = profile
                self.status = "connected"
                return 200, "Conta conectada. Pode fechar esta janela."
            except DomainError as error:
                self.error = error
                if self.status != "denied":
                    self.status = "failed"
                return 400, "Nao foi possivel concluir. Consulte o diagnostico local sanitizado."
            except Exception:
                self.status = "failed"
                self.error = DomainError("AUTH_REQUIRED", "Falha interna de autorizacao; inicie uma nova transacao.")
                return 500, "Falha de autorizacao. Nenhum segredo foi registrado."
            finally:
                self.done.set()
                # shutdown runs outside the serve_forever thread and after lock release.
                threading.Thread(target=self.close_listener, daemon=True).start()

    def refresh(self):
        with self.lock:
            record = self.vault.load()
            if not record or record.state != "active":
                raise DomainError("AUTH_REQUIRED", "Sem credencial renovavel; reautorize, sem reapresentar refresh antigo.")
            # Durable preflight marker closes the crash/timeout retry window.
            self.vault.save(record.model_copy(update={"state": "refresh_in_flight"}))
            raw = self.client.exchange({
                "grant_type": "refresh_token", "client_id": self.config.client_id,
                "client_secret": self.config.client_secret.get_secret_value(),
                "refresh_token": record.refresh_token.get_secret_value(),
            })
            renewed = self._tokens(raw, expected_seller=record.seller_id)
            if hmac.compare_digest(renewed.refresh_token.get_secret_value(), record.refresh_token.get_secret_value()):
                raise DomainError("OAUTH_RESULT_UNCERTAIN", "API nao rotacionou refresh token; reautorize.")
            self.vault.save(renewed)
            return renewed

    def get_profile(self, *, already_renewed=False):
        with self.lock:
            record = self.vault.load()
            if not record or record.state != "active":
                raise DomainError("AUTH_REQUIRED", "Conta nao autorizada ou renovacao de resultado incerto.")
            renewed = already_renewed
            if record.expires_at <= time.time() + 60 and not renewed:
                record = self.refresh()
                renewed = True
            try:
                profile = self.client.profile(record.access_token.get_secret_value())
            except DomainError as error:
                if error.code != "AUTH_REQUIRED":
                    raise
                if renewed:
                    self.vault.save(record.model_copy(update={"state": "reauthorize"}))
                    raise DomainError("AUTH_REQUIRED", "Token renovado foi recusado; reautorize.") from None
                record = self.refresh()  # One renewal and one GET replay, never a loop.
                try:
                    profile = self.client.profile(record.access_token.get_secret_value())
                except DomainError as second_error:
                    if second_error.code == "AUTH_REQUIRED":
                        self.vault.save(record.model_copy(update={"state": "reauthorize"}))
                    raise
            if profile.seller_id != record.seller_id:
                self.vault.save(record.model_copy(update={"state": "reauthorize"}))
                raise DomainError("PERMISSION_DENIED", "Identidade nao corresponde ao perfil no cofre.")
            return profile

    def prepare_reauthorization(self):
        with self.lock:
            record = self.vault.load()
            if record:
                self.vault.save(record.model_copy(update={"state": "reauthorize"}))
            # Keep previous seller binding until callback has confirmed it.

    def authorize_again(self, open_browser=True):
        # Deliberate new transaction after failure; do not silently switch accounts.
        self.prepare_reauthorization()
        return self.start_oauth(open_browser=open_browser, reauthorize=True)


def main():
    parser = argparse.ArgumentParser(description="Diagnostico administrativo OAuth local; nunca imprime tokens.")
    parser.add_argument("action", choices=["check", "tls-only", "authorize", "profile", "refresh", "reauthorize"])
    parser.add_argument("--seconds", type=int, default=120)
    args = parser.parse_args()
    try:
        config = AuthConfig.load()
        with AuthManager(config) as manager:
            if args.action == "check":
                config.tls_context()
                # Secure synthetic write/read/delete, not production credentials.
                account = "diagnostic-" + secrets.token_hex(16)
                value = secrets.token_urlsafe(32)
                backend = manager.vault.backend
                try:
                    backend.set_password(WindowsVault.SERVICE, account, value)
                    if backend.get_password(WindowsVault.SERVICE, account) != value:
                        raise DomainError("SECURE_STORAGE_UNAVAILABLE", "Readback sintetico do cofre falhou.")
                finally:
                    try:
                        backend.delete_password(WindowsVault.SERVICE, account)
                    except Exception:
                        raise DomainError("SECURE_STORAGE_UNAVAILABLE", "Falha ao remover credencial diagnostica.") from None
                result = success({"configuration": "valid", "vault": "WinVaultKeyring", "certificate_loaded": True,
                                  "browser_trust": "not_checked", "pkce": "S256", "redirect_uri": REDIRECT_URI})
            elif args.action == "tls-only":
                if not 1 <= args.seconds <= 300:
                    raise DomainError("INVALID_ARGUMENT", "seconds deve estar entre 1 e 300.")
                manager._start_listener(diagnostic=True)
                print(json.dumps(success({"status": "tls_ready", "redirect_uri": REDIRECT_URI})), file=sys.stderr, flush=True)
                time.sleep(args.seconds)
                result = success({"status": "closed", "oauth_executed": False})
            elif args.action in {"authorize", "reauthorize"}:
                # Refuse to open a browser with an untrusted local certificate.
                import urllib.request
                manager._start_listener(diagnostic=True)
                try:
                    urllib.request.urlopen(REDIRECT_URI, context=ssl.create_default_context(), timeout=5).close()
                except Exception:
                    raise DomainError("CONFIGURATION_ERROR", "HTTPS nao e confiavel pelo Windows; nao abra OAuth nem ignore o aviso. CA nao foi instalada.") from None
                finally:
                    manager.close_listener()
                pending = manager.authorize_again() if args.action == "reauthorize" else manager.start_oauth()
                if pending["status"] == "pending":
                    print(json.dumps(success({"status": "pending", "browser_open_requested": True})), file=sys.stderr, flush=True)
                    manager.done.wait(340)
                    if manager.error:
                        raise manager.error
                    if manager.status != "connected":
                        raise DomainError("AUTH_REQUIRED", "Autorizacao nao foi concluida; listener encerrado.")
                    if manager.profile_result is None:
                        raise DomainError("AUTH_REQUIRED", "Identidade ainda nao confirmada.")
                    result = success(manager.profile_result.model_dump(), source="mercadolivre_api")
                else:
                    result = success(pending, source="mercadolivre_api")
            else:
                if args.action == "refresh":
                    manager.refresh()
                result = success(manager.get_profile(already_renewed=args.action == "refresh").model_dump(), source="mercadolivre_api")
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 0
    except DomainError as error:
        print(json.dumps(error.result(), ensure_ascii=False), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print(json.dumps(DomainError("AUTH_REQUIRED", "Operacao interrompida; recursos liberados.").result()), file=sys.stderr)
        return 130
    except Exception:
        print(json.dumps(DomainError("CONFIGURATION_ERROR", "Falha local; nenhum traceback ou segredo foi emitido.").result()), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
