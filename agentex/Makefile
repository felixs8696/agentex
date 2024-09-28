# Makefile

install:
	poetry install

# Command to run everything in development mode using Docker Compose
dev:
	docker-compose up --build

# Command to stop and remove all services
stop:
	docker-compose down

# Command to clean up services, removing containers, networks, and volumes
clean:
	docker-compose down --volumes --remove-orphans

# Command to run in production mode
prod:
	ENV=production cargo run

# Command to test (just an example)
test:
	poetry run pytest --cov=agentex
