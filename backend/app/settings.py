from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ProviderSettings:
    veitur_api_token: str | None
    veitur_permanent_number: str | None
    hsveitur_public_token: str | None
    hsveitur_private_token: str | None
    hsveitur_customer_id: str | None
    zaptec_username: str | None
    zaptec_password: str | None
    location_latitude: str | None
    location_longitude: str | None

    veitur_base_url: str
    hsveitur_base_url: str
    zaptec_base_url: str
    zaptec_token_url: str


def load_provider_settings() -> ProviderSettings:
    return ProviderSettings(
        veitur_api_token=os.getenv("VEITUR_API_TOKEN"),
        veitur_permanent_number=os.getenv("VEITUR_PERMANENT_NUMBER"),
        hsveitur_public_token=os.getenv("HSVEITUR_PUBLIC_TOKEN"),
        hsveitur_private_token=os.getenv("HSVEITUR_PRIVATE_TOKEN"),
        hsveitur_customer_id=os.getenv("HSVEITUR_CUSTOMER_ID"),
        zaptec_username=os.getenv("ZAPTEC_USERNAME"),
        zaptec_password=os.getenv("ZAPTEC_PASSWORD"),
        location_latitude=os.getenv("LOCATION_LATITUDE"),
        location_longitude=os.getenv("LOCATION_LONGITUDE"),
        veitur_base_url=os.getenv("VEITUR_BASE_URL", "https://api.veitur.is"),
        hsveitur_base_url=os.getenv("HSVEITUR_BASE_URL", "https://www.hsveitur.is/umbraco/api"),
        zaptec_base_url=os.getenv("ZAPTEC_BASE_URL", "https://api.zaptec.com"),
        zaptec_token_url=os.getenv("ZAPTEC_TOKEN_URL", "https://api.zaptec.com/oauth/token"),
    )
