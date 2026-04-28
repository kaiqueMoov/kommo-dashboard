import httpx

from app.core.config import settings


class KommoClient:
    def __init__(self) -> None:
        self.base_url = settings.KOMMO_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.KOMMO_LONG_LIVED_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_pipeline_statuses(self, pipeline_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/v4/leads/pipelines/{pipeline_id}/statuses",
                headers=self.headers,
            )

        if not response.is_success:
            return {
                "status_code": response.status_code,
                "text": response.text,
            }

        return response.json()
        

    async def get_account(self) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/v4/account",
                headers=self.headers,
            )

            if not response.is_success:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                }

            return response.json()

    async def get_users(self, page: int = 1, limit: int = 250) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/v4/users",
                headers=self.headers,
                params={
                    "page": page,
                    "limit": limit,
                },
            )

            if not response.is_success:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                }

            return response.json()

    async def get_pipelines(self) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/v4/leads/pipelines",
                headers=self.headers,
            )

            if not response.is_success:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                }

            return response.json()
        



async def get_pipelines(self) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{self.base_url}/api/v4/leads/pipelines",
            headers=self.headers,
        )

        if not response.is_success:
            return {
                "status_code": response.status_code,
                "text": response.text,
            }

        return response.json()


async def get_pipeline_statuses(self, pipeline_id: int) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{self.base_url}/api/v4/leads/pipelines/{pipeline_id}/statuses",
            headers=self.headers,
        )

        if not response.is_success:
            return {
                "status_code": response.status_code,
                "text": response.text,
            }

        return response.json()

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

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/v4/leads",
                headers=self.headers,
                params=params,
            )

            if not response.is_success:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                }

            return response.json()

    async def get_lead_by_id(self, lead_id: int) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/v4/leads/{lead_id}",
                headers=self.headers,
                params={
                    "with": "contacts",
                },
            )

            if not response.is_success:
                return {
                    "status_code": response.status_code,
                    "text": response.text,
                }

            return response.json()