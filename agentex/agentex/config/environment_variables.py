from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from agentex.utils.model_utils import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class EnvVarKeys:
    ENV = "ENV"
    OPENAI_API_KEY = "OPENAI_API_KEY"


class Environments(str, Enum):
    DEV = "development"
    PROD = "production"


refreshed_environment_variables = None


class EnvironmentVariables(BaseModel):
    ENV: Optional[str] = Environments.DEV
    OPENAI_API_KEY: Optional[str]

    @classmethod
    def refresh(cls) -> Optional[EnvironmentVariables]:
        global refreshed_environment_variables
        if refreshed_environment_variables is not None:
            return refreshed_environment_variables

        if os.environ.get(EnvVarKeys.ENV) == Environments.DEV:
            load_dotenv(dotenv_path=Path(PROJECT_ROOT / '.env'), override=True)
        environment_variables = EnvironmentVariables(
            ENV=os.environ.get(EnvVarKeys.ENV),
            OPENAI_API_KEY=os.environ.get(EnvVarKeys.OPENAI_API_KEY),
        )
        refreshed_environment_variables = environment_variables
        return refreshed_environment_variables
