from abc import abstractmethod, ABC
from enum import Enum
from typing import Dict, Literal, Optional


class Method(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class HttpPort(ABC):

    @abstractmethod
    async def async_call(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        url: str,
        payload: Optional[Dict] = None
    ) -> Dict:
        pass

    @abstractmethod
    def call(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        url: str,
        payload: Optional[Dict] = None
    ) -> Dict:
        pass
