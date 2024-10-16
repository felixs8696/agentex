from datetime import timedelta
from typing import Optional, TypeVar, List, Union, Type

from temporalio import workflow
from temporalio.common import RetryPolicy

from agentex.utils.model_utils import BaseModel

T = TypeVar("T", bound="BaseModel")


async def execute_workflow_activity(
    activity_name: str,
    arg: Union[BaseModel, str, int, float, bool, dict, list],
    start_to_close_timeout: Optional[timedelta],
    retry_policy: Optional[RetryPolicy] = None,
    response_model: Optional[Type[T]] = None,
) -> Union[List[T], T]:
    if start_to_close_timeout is None:
        start_to_close_timeout = timedelta(seconds=10)
    if retry_policy is None:
        retry_policy = RetryPolicy(maximum_attempts=0)

    response = await workflow.execute_activity(
        activity=activity_name,
        arg=arg,
        start_to_close_timeout=start_to_close_timeout,
        retry_policy=retry_policy,
    )
    if isinstance(response, dict) and response_model:
        return response_model.from_dict(response)
    elif isinstance(response, list):
        return [response_model.from_dict(item) for item in response]
    return response
