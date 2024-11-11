from enum import Enum


class AgentActivity(str, Enum):
    BUILD_AGENT_IMAGE = "build_agent_image"
    GET_BUILD_JOB = "get_build_job"
    DELETE_BUILD_JOB = "delete_build_job"
    CREATE_AGENT_DEPLOYMENT = "create_agent_deployment"
    CREATE_AGENT_SERVICE = "create_agent_service"
    GET_AGENT_DEPLOYMENT = "get_agent_deployment"
    GET_AGENT_SERVICE = "get_agent_service"
    CALL_AGENT_SERVICE = "call_agent_service"
    DELETE_AGENT_DEPLOYMENT = "delete_agent_deployment"
    DELETE_AGENT_SERVICE = "delete_agent_service"
    UPDATE_AGENT_STATUS = "update_agent_status"
    UPDATE_AGENT = "update_agent"
