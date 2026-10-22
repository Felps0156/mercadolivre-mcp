"""Minimal safe contracts for the accompanied OAuth implementation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class DomainError(Exception):
    """An actionable error whose message never includes an upstream payload."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def result(self) -> dict:
        return {
            "success": False, "data": None, "period": None,
            "metadata": {}, "warnings": [],
            "error": {"code": self.code, "message": self.message,
                      "retryable": False, "retry_after_seconds": None},
        }


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
    return {
        "success": True, "data": data, "period": None,
        "metadata": {"schema_version": "1.0", **metadata},
        "warnings": [], "error": None,
    }
