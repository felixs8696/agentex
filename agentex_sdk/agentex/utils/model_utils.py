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

    @classmethod
    def from_yaml(cls: Type[T], file_path: str) -> T:
        """
        Returns an instance of this class by deserializing from a YAML file.

        :param file_path: The path to the YAML file.
        :return: An instance of this class.
        """
        yaml_dict = load_yaml_file(file_path=file_path)
        class_object = cls.from_dict(obj=yaml_dict)
        return class_object

    def to_json(self, *args, **kwargs) -> str:
        return self.model_dump_json(*args, **kwargs)

    def to_dict(self, *args, **kwargs) -> Dict[str, Any]:
        return self.model_dump(*args, **kwargs)
