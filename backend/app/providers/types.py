from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import httpx


class FailureCategory(StrEnum):
    AUTH = "auth"
    NETWORK = "network"
    SCHEMA = "schema"
    EMPTY = "empty"
    RATE_LIMIT = "rate_limit"


@dataclass(slots=True)
class ProviderError(Exception):
    provider: str
    category: FailureCategory
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        status_text = f" (status={self.status_code})" if self.status_code is not None else ""
        return f"{self.provider}:{self.category}{status_text} {self.message}"


def classify_http_failure(status_code: int) -> FailureCategory:
    if status_code in {401, 403}:
        return FailureCategory.AUTH
    if status_code == 429:
        return FailureCategory.RATE_LIMIT
    if status_code in {404, 422}:
        return FailureCategory.SCHEMA
    if status_code == 204:
        return FailureCategory.EMPTY
    if status_code >= 500:
        return FailureCategory.NETWORK
    return FailureCategory.SCHEMA


def raise_for_response(provider: str, response: httpx.Response) -> None:
    if response.is_success:
        return
    category = classify_http_failure(response.status_code)
    raise ProviderError(
        provider=provider,
        category=category,
        message=response.text[:300],
        status_code=response.status_code,
    )
