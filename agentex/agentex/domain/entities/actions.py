from typing import Dict, Any, Optional

from pydantic import Field

from agentex.utils.model_utils import BaseModel


class ActionSchema(BaseModel):
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


class Action(BaseModel):
    """
    Every Agent server will expose a REST API at the root route that will allow Agentex to fetch the agent's metadata.
    This includes a list of actions that the agent can perform which are defined by this spec.
    """
    schema: ActionSchema = Field(
        ...,
        description="The JSON schema describing the parameters that the action takes in"
    )
    test_payload: Optional[Dict[str, Any]] = Field(
        None,
        description="The payload to use when testing the action."
    )
