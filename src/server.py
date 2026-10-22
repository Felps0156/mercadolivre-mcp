"""Minimal FastMCP stdio composition; commercial tools are later sprints."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import sys
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv
from fastmcp import FastMCP

from .client import MercadoLivreClient
from .schemas import DomainError

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ServerConfig:
    timezone: str
    log_level: str
    connect_timeout: float
    read_timeout: float
    max_analysis_requests: int
    max_analysis_seconds: int

    @classmethod
    def load(cls) -> "ServerConfig":
        # OAuth credentials are optional at this stage. Never display env values.
        load_dotenv(ROOT / ".env", override=False)
        timezone_name = os.environ.get("BUSINESS_TIMEZONE", "America/Sao_Paulo")
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            raise DomainError("CONFIGURATION_ERROR", "BUSINESS_TIMEZONE invalido ou indisponivel.") from None
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise DomainError("CONFIGURATION_ERROR", "LOG_LEVEL invalido.")

        def number(name: str, default: str, maximum: float, *, whole: bool = False):
            value = os.environ.get(name, default)
            try:
                parsed = int(value) if whole else float(value)
                if not 0 < parsed <= maximum or (not whole and not parsed < float("inf")):
                    raise ValueError
                return parsed
            except (TypeError, ValueError):
                raise DomainError("CONFIGURATION_ERROR", f"{name} invalido ou fora da faixa.") from None

        return cls(
            timezone=timezone_name, log_level=level,
            connect_timeout=number("HTTP_CONNECT_TIMEOUT_SECONDS", "5", 30),
            read_timeout=number("HTTP_READ_TIMEOUT_SECONDS", "30", 60),
            max_analysis_requests=int(number("MAX_ANALYSIS_REQUESTS", "500", 500, whole=True)),
            max_analysis_seconds=int(number("MAX_ANALYSIS_SECONDS", "180", 180, whole=True)),
        )


class SafeFormatter(logging.Formatter):
    """Redact common secret shapes; application events never include payloads."""

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        text = re.sub(r"(?i)(https?://[^\s?]+)\?[^\s]+", r"\1?[REDACTED]", text)
        text = re.sub(r"(?i)\b(Bearer\s+)[^\s,;]+", r"\1[REDACTED]", text)
        text = re.sub(r"(?i)\b((?:client_secret|access_token|refresh_token|code|state|code_verifier)=)[^\s&;,]+", r"\1[REDACTED]", text)
        return re.sub(r'(?i)("(?:client_secret|access_token|refresh_token|code|state|code_verifier)"\s*:\s*")[^"]*(")', r'\1[REDACTED]\2', text)


def configure_logging(level: str) -> logging.Logger:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(SafeFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.WARNING)
    # HTTP library debug output may include headers/bodies; never enable it.
    for name in ("urllib3", "requests", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logger = logging.getLogger("diasmoto.mcp")
    logger.setLevel(level)
    return logger


def build_server(config: ServerConfig) -> FastMCP:
    @asynccontextmanager
    async def lifespan(_server):
        client = MercadoLivreClient(connect_timeout=config.connect_timeout,
                                    read_timeout=config.read_timeout)
        logger = logging.getLogger("diasmoto.mcp")
        request_id = uuid4().hex
        logger.info("event=server_started request_id=%s", request_id)
        try:
            yield {"client": client, "config": config}
        finally:
            client.close()
            logger.info("event=server_stopped request_id=%s", request_id)

    # Do not register placeholders: the 8 real tools belong to Sprints 2–5.
    return FastMCP("dias-moto-mercadolivre", lifespan=lifespan)


def main() -> int:
    try:
        config = ServerConfig.load()
        configure_logging(config.log_level)
        build_server(config).run(transport="stdio", show_banner=False)
        return 0
    except DomainError as error:
        print(f"{error.code}: {error.message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
