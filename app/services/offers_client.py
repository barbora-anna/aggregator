"""HTTP client for the external offers service."""

import logging
from uuid import UUID

import httpx

from app.config import settings
from app.schemas import ExternalAuthResponse, ExternalOffer, ExternalRegistrationResponse

log = logging.getLogger(__name__)

_instance: "OffersClient | None" = None


class OffersClient:
    def __init__(self) -> None:
        self.base_url = settings.offers_service_url.rstrip("/")
        self.refresh_token = settings.offers_refresh_token.get_secret_value()
        self.access_token: str | None = None
        self._client = httpx.AsyncClient()

    @classmethod
    def get(cls) -> "OffersClient":
        """Return a shared singleton instance."""
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    @classmethod
    async def close(cls) -> None:
        """Close the shared instance's HTTP client."""
        global _instance
        if _instance is not None:
            await _instance._client.aclose()
            _instance = None

    async def _authenticate(self) -> None:
        """Exchange refresh token for access token."""
        response = await self._client.post(
            f"{self.base_url}/api/v1/auth",
            headers={"Bearer": self.refresh_token},
        )
        response.raise_for_status()
        data = ExternalAuthResponse.model_validate(response.json())
        self.access_token = data.access_token
        log.info("Authenticated with offers service")

    async def ensure_authenticated(self) -> None:
        """Authenticate if no valid token is cached."""
        if not self.access_token:
            await self._authenticate()

    def _auth_headers(self) -> dict[str, str]:
        return {"Bearer": self.access_token}

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Make a request, re-authenticate on 401 and retry once."""
        if not self.access_token:
            await self._authenticate()

        kwargs.setdefault("headers", {}).update(self._auth_headers())
        response = await self._client.request(method, url, **kwargs)

        if response.status_code == 401:
            log.info("Token expired, re-authenticating...")
            await self._authenticate()
            kwargs["headers"].update(self._auth_headers())
            response = await self._client.request(method, url, **kwargs)

        response.raise_for_status()
        return response

    async def register_product(self, product_id: UUID, name: str, description: str | None) -> UUID:
        """Register a product with the offers service. Returns external ID."""
        response = await self._request_with_retry(
            "POST",
            f"{self.base_url}/api/v1/products/register",
            json={"id": str(product_id), "name": name, "description": description or ""},
        )
        data = ExternalRegistrationResponse.model_validate(response.json())
        return data.id

    async def get_offers(self, product_id: UUID) -> list[ExternalOffer]:
        """Fetch offers for a product."""
        response = await self._request_with_retry(
            "GET",
            f"{self.base_url}/api/v1/products/{product_id}/offers",
        )
        return [ExternalOffer.model_validate(o) for o in response.json()]