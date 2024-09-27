import litellm
from litellm.types.completion import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
)


class Message(litellm.Message):
    pass


class SystemMessage(ChatCompletionSystemMessageParam):
    pass


class UserMessage(ChatCompletionUserMessageParam):
    pass


class AssistantMessage(ChatCompletionAssistantMessageParam):
    pass


class FunctionMessage(ChatCompletionFunctionMessageParam):
    pass
