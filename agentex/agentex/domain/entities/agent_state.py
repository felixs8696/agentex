from collections import defaultdict
from typing import List, Dict, Any, Optional

from pydantic import Field

from agentex.domain.entities.messages import Message
from agentex.utils.model_utils import BaseModel


class Thread(BaseModel):
    messages: List[Message] = Field(
        default_factory=list,
    )


class AgentState(BaseModel):
    """State object that holds the agent's transaction history and context."""
    threads: Optional[Dict[str, Thread]] = Field(
        default_factory=lambda: defaultdict(Thread),
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
    )
