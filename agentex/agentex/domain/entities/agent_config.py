from litellm.types.completion import CompletionRequest

from agentex.utils.model_utils import BaseModel


class AgentConfig(CompletionRequest, BaseModel):
    pass
