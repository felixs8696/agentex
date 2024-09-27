# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry globally
RUN pip install poetry

# Disable Poetry's virtual environment creation
RUN poetry config virtualenvs.create false

# Copy only dependency management files first to take advantage of Docker caching
COPY pyproject.toml poetry.lock /app/

# Install dependencies (only re-run when pyproject.toml or poetry.lock changes)
ENV POETRY_CACHE_DIR=/opt/.cache
RUN poetry install --compile --no-ansi --no-interaction && \
    rm -rf $POETRY_CACHE_DIR

# Copy the rest of the application code
COPY . /app

# Expose the FastAPI port
EXPOSE 5003

# Run the FastAPI app
CMD ["uvicorn", "agentex.api.app:app", "--host", "0.0.0.0", "--port", "5003", "--reload"]
