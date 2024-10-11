import json
from typing import Dict, Any, List, Optional

from pydantic import Field, model_validator

from agentex.domain.entities.agents import AgentStatus
from agentex.utils.model_utils import BaseModel


class CreateActionRequest(BaseModel):
    name: str = Field(
        ...,
        description="The name of the action."
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


class GetActionResponse(BaseModel):
    id: str = Field(
        ...,
        title="Unique Action ID",
    )
    name: str = Field(
        ...,
        description="The name of the action."
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
    status: AgentStatus = Field(
        ...,
        description="The status of the action."
    )


class CreateActionResponse(GetActionResponse):
    pass
