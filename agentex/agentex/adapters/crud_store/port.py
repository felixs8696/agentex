from abc import ABC, abstractmethod
from typing import Annotated, List, TypeVar, Generic, Optional

from fastapi import Depends

T = TypeVar("T")


class CRUDRepository(ABC, Generic[T]):

    @abstractmethod
    async def create(self, item: T) -> T:
        pass

    @abstractmethod
    async def batch_create(self, items: List[T]) -> List[T]:
        pass

    @abstractmethod
    async def get(self, id: Optional[str] = None, name: Optional[str] = None) -> T:
        pass

    @abstractmethod
    async def batch_get(self, ids: Optional[List[str]] = None, names: Optional[List[str]] = None) -> List[T]:
        pass

    @abstractmethod
    async def update(self, item: T) -> T:
        pass

    @abstractmethod
    async def batch_update(self, items: List[T]) -> List[T]:
        pass

    @abstractmethod
    async def delete(self, id: Optional[str] = None, name: Optional[str] = None) -> None:
        pass

    @abstractmethod
    async def batch_delete(self, ids: Optional[List[str]] = None, names: Optional[List[str]] = None) -> None:
        pass

    @abstractmethod
    async def list(self) -> List[T]:
        pass


DCRUDRepository = Annotated[CRUDRepository, Depends(CRUDRepository)]
