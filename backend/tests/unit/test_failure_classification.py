from __future__ import annotations

from app.providers.types import FailureCategory, classify_http_failure


def test_auth_status_codes_are_classified_as_auth() -> None:
    assert classify_http_failure(401) == FailureCategory.AUTH
    assert classify_http_failure(403) == FailureCategory.AUTH


def test_rate_limit_status_code_is_classified() -> None:
    assert classify_http_failure(429) == FailureCategory.RATE_LIMIT


def test_empty_status_code_is_classified() -> None:
    assert classify_http_failure(204) == FailureCategory.EMPTY


def test_server_status_codes_are_classified_as_network() -> None:
    assert classify_http_failure(500) == FailureCategory.NETWORK
    assert classify_http_failure(503) == FailureCategory.NETWORK


def test_unhandled_status_code_defaults_to_schema() -> None:
    assert classify_http_failure(418) == FailureCategory.SCHEMA
