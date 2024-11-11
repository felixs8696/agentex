from enum import Enum

from agentex.domain.workflows.constants import DEFAULT_ROOT_THREAD_NAME
from agentex.utils.model_utils import BaseModel


class SignalName(str, Enum):
    INSTRUCT = "instruct"
    APPROVE = "approve"


class QueryName(str, Enum):
    GET_EVENT_LOG = "get_event_log"


class HumanInstruction(BaseModel):
    task_id: str
    prompt: str
    thread_name: str = DEFAULT_ROOT_THREAD_NAME
