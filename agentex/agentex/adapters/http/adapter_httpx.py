from typing import Annotated, Optional, Dict, Literal

import httpx
from fastapi import Depends

from agentex.adapters.http.port import HttpPort
from agentex.utils.logging import make_logger

logger = make_logger(__name__)


class HttpxGateway(HttpPort):

    async def async_call(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        url: str,
        payload: Optional[Dict] = None
    ) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, json=payload)
            response.raise_for_status()
            return response.json()

    async def call(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        url: str,
        payload: Optional[Dict] = None
    ) -> Dict:
        response = httpx.request(method, url, json=payload)
        response.raise_for_status()
        return response.json()


DHttpxGateway = Annotated[HttpxGateway, Depends(HttpxGateway)]
