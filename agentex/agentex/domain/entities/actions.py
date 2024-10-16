from typing import Dict, Any

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class Action(BaseModel):
    id: str = Field(
        ...,
        title="Unique Action ID",
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
