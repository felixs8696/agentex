from typing import List, Optional, Union, Type

from litellm.types.completion import CompletionRequest

from agentex.domain.entities.agents import Agent
from agentex.utils.model_utils import BaseModel


class LLMConfig(BaseModel):
    model: str
    messages: List = []
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    stream_options: Optional[dict] = None
    stop: Optional[Union[str, list]] = None
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[dict] = None
    response_format: Optional[Union[dict, Type[BaseModel]]] = None
    seed: Optional[int] = None
    tools: Optional[List] = None
    tool_choice: Optional[str] = None
    parallel_tool_calls: Optional[bool] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None


class AgentConfig(BaseModel):
    agent: Agent
    llm_config: LLMConfig
