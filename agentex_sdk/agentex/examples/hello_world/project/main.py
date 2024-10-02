import json
import os
import functools


class Agentex:
    """SDK to facilitate function execution with parameters from a file."""

    PARAMS_PATH = '/app/config/params.json'
    RESULT_PATH = '/app/output/result.json'

    @classmethod
    def action(cls, func):
        """Decorator to wrap user-defined functions for automatic parameter loading and result saving."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Load parameters from the specified file
            if os.path.exists(cls.PARAMS_PATH):
                with open(cls.PARAMS_PATH, 'r') as param_file:
                    parameters = json.load(param_file)
            else:
                raise FileNotFoundError(f"Parameters file not found: {cls.PARAMS_PATH}")

            # Execute the user's function with the loaded parameters
            result = func(**parameters)

            # Save the result to the specified file
            with open(cls.RESULT_PATH, 'w') as result_file:
                json.dump(result, result_file)

            return result

        return wrapper


# Instantiate the SDK to allow usage in user code
agentex = Agentex()


@agentex.action
def execute(name: str) -> dict:
    """Custom function that takes a name and returns a greeting message."""
    return {"message": f"Hello, {name}!"}


if __name__ == "__main__":
    execute()
