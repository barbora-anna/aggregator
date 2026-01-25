"""HTTP client for the external offers service."""

import logging
from uuid import UUID

import httpx

from app.config import settings
from app.schemas import ExternalAuthResponse, ExternalOffer, ExternalRegistrationResponse

log = logging.getLogger(__name__)


class OffersClient:
    def __init__(self) -> None:
        self.base_url = settings.offers_service_url.rstrip("/")
        self.refresh_token = settings.offers_refresh_token
        self.access_token: str | None = None

    async def _authenticate(self, client: httpx.AsyncClient) -> None:
        """Exchange refresh token for access token."""
        response = await client.post(
            f"{self.base_url}/api/v1/auth",
            json={"refresh_token": self.refresh_token},
        )
        response.raise_for_status()
        data = ExternalAuthResponse.model_validate(response.json())
        self.access_token = data.access_token
        log.info("Authenticated with offers service")

    def _auth_headers(self) -> dict[str, str]:
        return {"Bearer": self.access_token}

    async def _request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Make request, re-authenticate on 401 and retry once."""
        if not self.access_token:
            await self._authenticate(client)

        kwargs.setdefault("headers", {}).update(self._auth_headers())
        response = await client.request(method, url, **kwargs)

        if response.status_code == 401:
            log.info("Token expired, re-authenticating...")
            await self._authenticate(client)
            kwargs["headers"].update(self._auth_headers())
            response = await client.request(method, url, **kwargs)

        response.raise_for_status()
        return response

    async def register_product(self, product_id: UUID, name: str, description: str | None) -> UUID:
        """Register a product with the offers service. Returns external ID."""
        async with httpx.AsyncClient() as client:
            response = await self._request_with_retry(
                client,
                "POST",
                f"{self.base_url}/api/v1/products/register",
                json={"id": str(product_id), "name": name, "description": description or ""},
            )
            data = ExternalRegistrationResponse.model_validate(response.json())
            return data.id

    async def get_offers(self, product_id: UUID) -> list[ExternalOffer]:
        """Fetch offers for a product."""
        async with httpx.AsyncClient() as client:
            response = await self._request_with_retry(
                client,
                "GET",
                f"{self.base_url}/api/v1/products/{product_id}/offers",
            )
            return [ExternalOffer.model_validate(o) for o in response.json()]
