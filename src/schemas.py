"""Safe contracts for the OAuth slice and MCP foundation."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import re
from typing import Generic, Literal, TypeVar
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_serializer


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Money(Contract):
    amount: Decimal
    currency_id: str = Field(pattern=r"^[A-Z]{3}$")

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, value: Decimal) -> str:
        if not value.is_finite():
            raise ValueError("Non-finite money is not serializable")
        return format(value, "f")


class Period(Contract):
    date_from: date
    date_to: date
    effective_start: datetime
    effective_end_exclusive: datetime
    timezone: str
    convention: Literal["created_paid_v1"] = "created_paid_v1"
    period_is_open: bool


class ToolError(Contract):
    code: str
    message: str
    retryable: bool = False
    retry_after_seconds: int | None = None


class Warning(Contract):
    code: str
    message: str


class Pagination(Contract):
    has_more: bool
    next_offset: int | None = None
    next_cursor: str | None = None


class Metadata(Contract):
    schema_version: Literal["1.0"] = "1.0"
    source: str = "local_diagnostic"
    seller_id: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    collection_started_at: datetime | None = None
    collection_finished_at: datetime | None = None
    endpoints_used: list[str] = Field(default_factory=list)
    records_processed: int | None = None
    api_total: int | None = None
    has_more: bool | None = None
    next_offset: int | None = None
    next_cursor: str | None = None
    collection_complete: bool | None = None
    period_is_open: bool | None = None
    coverage_reason: str | None = None
    methodology_version: str | None = None
    request_id: str = Field(default_factory=lambda: uuid4().hex)


T = TypeVar("T")


class ToolResult(Contract, Generic[T]):
    success: bool
    data: T | None
    period: Period | None = None
    metadata: Metadata = Field(default_factory=Metadata)
    warnings: list[Warning] = Field(default_factory=list)
    error: ToolError | None = None


class DomainError(Exception):
    """An actionable error whose message never includes an upstream payload."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def result(self) -> dict:
        return ToolResult[dict](success=False, data=None,
                                error=ToolError(code=self.code, message=self.message)).model_dump(mode="json")


def require_id(value: str, *, item: bool = False) -> str:
    pattern = r"MLB[0-9]+" if item else r"[0-9]+"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise DomainError("INVALID_ARGUMENT", "ID invalido para o tipo solicitado.")
    return value


def require_limit(value: int, *, minimum: int = 1, maximum: int = 50) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise DomainError("INVALID_ARGUMENT", f"Limite deve ser inteiro de {minimum} a {maximum}.")
    return value


def require_offset(value: int) -> int:
    if type(value) is not int or value < 0:
        raise DomainError("INVALID_ARGUMENT", "Offset deve ser inteiro nao negativo.")
    return value


def parse_period(date_from: str, date_to: str, *, timezone_name: str = "America/Sao_Paulo", max_days: int = 120) -> Period:
    """Inclusive public dates -> half-open local interval; no silent coercion."""
    try:
        if not isinstance(date_from, str) or not isinstance(date_to, str):
            raise ValueError
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_from) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_to):
            raise ValueError
        start, end = date.fromisoformat(date_from), date.fromisoformat(date_to)
        tz = ZoneInfo(timezone_name)
        today = datetime.now(tz).date()
        if start > end or end > today or not 1 <= (end - start).days + 1 <= max_days:
            raise ValueError
        return Period(
            date_from=start, date_to=end,
            effective_start=datetime.combine(start, time.min, tzinfo=tz),
            effective_end_exclusive=datetime.combine(end + timedelta(days=1), time.min, tzinfo=tz),
            timezone=timezone_name, period_is_open=end == today,
        )
    except ZoneInfoNotFoundError:
        raise DomainError("CONFIGURATION_ERROR", "Fuso configurado indisponivel.") from None
    except (ValueError, OverflowError):
        raise DomainError("INVALID_DATE_RANGE", "Datas devem ser dias validos YYYY-MM-DD, nao futuros, em ordem e dentro do limite.") from None


class TokenRecord(BaseModel):
    """One logical record, serialized only inside the native Windows vault."""

    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    client_id: str = Field(pattern=r"^[0-9]+$")
    seller_id: str = Field(pattern=r"^[0-9]+$")
    access_token: SecretStr = Field(min_length=1)
    refresh_token: SecretStr = Field(min_length=1)
    expires_at: float = Field(gt=0)
    state: Literal["active", "refresh_in_flight", "reauthorize"] = "active"


class SellerProfile(BaseModel):
    """Only the identity fields required to confirm the grant; no PII."""

    model_config = ConfigDict(extra="forbid")
    seller_id: str = Field(pattern=r"^[0-9]+$")
    nickname: str
    country_id: str | None = None
    site_id: str | None = None


def success(data: dict, **metadata) -> dict:
    return ToolResult[dict](success=True, data=data,
                            metadata=Metadata(**metadata)).model_dump(mode="json")
