from agentex.utils.model_utils import BaseModel


class TaskRequest(BaseModel):
    prompt: str


class TaskResponse(BaseModel):
    content: str
