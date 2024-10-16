from typing import Optional, Dict, List

from pydantic import Field

from agentex.domain.entities.action_spec import ActionSpec
from agentex.utils.model_utils import BaseModel


class AgentSpec(BaseModel):
    """
    Every Agent server will expose a REST API at the root route that will allow Agentex to fetch the agent's metadata.
    """
    model: str = Field(
        ...,
        description="The LLM model powering the agent."
    )
    instructions: str = Field(
        ...,
        description="The instructions for the agent."
    )
    actions: Optional[List[ActionSpec]] = Field(
        default=None,
        description="The actions that the agent can perform."
    )
