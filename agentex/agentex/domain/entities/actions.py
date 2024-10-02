from enum import Enum
from typing import Dict, Any, Optional

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class PackagingMethod(str, Enum):
    DOCKER = "docker"


class Action(BaseModel):
    id: str = Field(
        ...,
        title="Unique Action ID",
    )
    packaging_method: PackagingMethod = Field(
        PackagingMethod.DOCKER,
        description="The method used to bundle the action code."
    )
    name: str = Field(
        ...,
        description="The name of the action. If you try to create a new action with the same name as an existing "
                    "action, the the version must be changed to create a new version of the action."
    )
    description: str = Field(
        ...,
        description="The description of the action."
    )
    parameters: Dict[str, Any] = Field(
        ...,
        description="The JSON schema describing the parameters that the action takes in"
    )
    test_payload: Dict[str, Any] = Field(
        ...,
        description="The payload to use when testing the action."
    )
    version: str = Field(
        ...,
        description="The version of the action."
    )
    docker_image: Optional[str] = Field(
        None,
        description="The URI of the image associated with the action. Only set if the packaging method is `docker`."
    )
