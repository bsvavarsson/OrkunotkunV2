from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any


REDACTED_KEYS = {
    "token",
    "authorization",
    "password",
    "secret",
    "apikey",
    "api_key",
}


def redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, nested in value.items():
            normalized_key = key.lower().replace("-", "_")
            if any(part in normalized_key for part in REDACTED_KEYS):
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = redact_payload(nested)
        return redacted

    if isinstance(value, list):
        return [redact_payload(item) for item in value]

    return value


def write_integration_evidence(provider: str, content: dict[str, Any]) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    evidence_dir = repo_root / "docs" / "integration-evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    output_path = evidence_dir / f"{provider}-latest.json"
    payload = {
        "provider": provider,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "content": redact_payload(content),
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path
