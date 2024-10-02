class AgentexException(Exception):
    """
    A general Agentex exception.
    """


class ClientError(AgentexException):
    """
    Raised when a client error occurs. Use this as an exception base class for all client
    exceptions.
    """


class ServiceError(AgentexException):
    """
    Raised when an error that is not caused by bad user input occurs within the service
    """
