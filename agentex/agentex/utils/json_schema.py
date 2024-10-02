from typing import Dict, Any

from jsonschema import validate as schema_validation, ValidationError

from agentex.domain.exceptions import ClientError


class JSONSchemaValidationError(ClientError):
    """
    Error raised when there is an issue with the JSON schema validation.
    """

    code = 400


def validate_payload(json_schema: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """Validate the payload against the JSON schema."""
    try:
        schema_validation(instance=payload, schema=json_schema)
    except ValidationError as e:
        raise JSONSchemaValidationError(f"Payload validation error: {e.message}")
