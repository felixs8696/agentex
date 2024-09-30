from typing import List, Dict, Any, Optional

from pydantic import Field

from agentex.domain.entities.messages import Message
from agentex.utils.model_utils import BaseModel


class AgentState(BaseModel):
    """State object that holds the agent's transaction history and context."""
    messages: Optional[List[Message]] = Field(
        default_factory=list,
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
    )
