from agentex.domain.exceptions import ClientError


class DuplicateItemError(ClientError):
    """
    Exception raised when an item already exists in the database.
    """
