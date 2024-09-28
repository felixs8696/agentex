import json
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel as PydanticBaseModel, ConfigDict

T = TypeVar("T", bound="BaseModel")


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, )

    @classmethod
    def from_model(cls: Type[T], model: Optional[T] = None) -> Optional[T]:
        if not model:
            return None
        return cls.model_validate(model)

    @classmethod
    def from_dict(cls: Type[T], obj: Optional[Dict[str, Any]] = None) -> Optional[T]:
        if not obj:
            return None
        return cls.model_validate(obj)

    @classmethod
    def from_json(cls: Type[T], json_str: Optional[str] = None) -> Optional[T]:
        if not json_str:
            return None
        return cls.model_validate_json(json_str)

    def to_json(self) -> str:
        return self.model_dump_json()

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
