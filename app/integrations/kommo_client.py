import httpx

from app.core.config import settings


class KommoClient:
    def __init__(self) -> None:
        self.base_url = (settings.KOMMO_BASE_URL or "").strip().rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.KOMMO_LONG_LIVED_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params,
            )

            if response.is_redirect:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                    "location": response.headers.get("location"),
                    "requested_url": str(response.request.url),
                }

            if not response.is_success:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                    "requested_url": str(response.request.url),
                }

            return response.json()

    async def get_account(self) -> dict:
        return await self._get("/api/v4/account")

    async def get_users(self, page: int = 1, limit: int = 250) -> dict:
        return await self._get(
            "/api/v4/users",
            params={
                "page": page,
                "limit": limit,
            },
        )

    async def get_leads(
        self,
        page: int = 1,
        limit: int = 250,
        created_from: int | None = None,
    ) -> dict:
        params = {
            "page": page,
            "limit": limit,
            "order[created_at]": "desc",
        }

        if created_from is not None:
            params["filter[created_at][from]"] = created_from

        return await self._get("/api/v4/leads", params=params)

    async def get_lead_by_id(self, lead_id: int) -> dict:
        return await self._get(
            f"/api/v4/leads/{lead_id}",
            params={"with": "contacts"},
        )

    async def get_lead_custom_fields(self) -> dict:
        return await self._get(
            "/api/v4/leads/custom_fields",
            params={"page": 1, "limit": 250},
        )