from abc import ABC, abstractmethod
from typing import Annotated, List, TypeVar, Generic, Optional

from fastapi import Depends

T = TypeVar("T")


class CRUDRepository(ABC, Generic[T]):

    @abstractmethod
    async def create(self, item: T) -> T:
        pass

    @abstractmethod
    async def get(self, id: Optional[str], name: Optional[str]) -> T:
        pass

    @abstractmethod
    async def update(self, item: T) -> T:
        pass

    @abstractmethod
    async def delete(self, id: Optional[str], name: Optional[str]) -> T:
        pass

    @abstractmethod
    async def list(self) -> List[T]:
        pass


DCRUDRepository = Annotated[CRUDRepository, Depends(CRUDRepository)]
