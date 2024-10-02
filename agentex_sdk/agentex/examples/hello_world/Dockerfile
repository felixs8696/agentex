# Use a lightweight Python image
FROM python:3.8-slim-buster

# Set up the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code from the project directory
COPY project /app/project

# Set the entrypoint to run FastAPI using Uvicorn
CMD ["python", "main.py"]
