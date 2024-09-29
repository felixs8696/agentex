# Makefile

install:
	poetry install

# Command to run everything in development mode using Docker Compose
dev:
	docker-compose down -v && docker-compose up --build

# Command to stop and remove all services
stop:
	docker-compose down

# Command to clean up services, removing containers, networks, and volumes
clean:
	docker-compose down --volumes --remove-orphans

# Command to create a new Alembic migration
migration:
	@echo "Starting PostgreSQL container..."
	docker-compose up -d postgres
	sleep 5 # Wait for PostgreSQL to start
	@echo "Running Alembic migrations..."
	# Run migrations from the database/migrations folder
	docker-compose run --rm -e ENV=development -w /app/database/migrations -v $(PWD)/database/migrations:/app/database/migrations agentex-backend alembic upgrade head
	@echo "Generating new migration..."
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is not defined. Please provide a name for the migration."; \
		exit 1; \
	fi; \
	# Generate a new migration from the database/migrations folder
	docker-compose run --rm -e ENV=development -w /app/database/migrations -v $(PWD)/database/migrations:/app/database/migrations agentex-backend alembic revision --autogenerate -m "$(NAME)"
	@echo "Migration generation completed."


clean-db:
	@echo "Stopping services..."
	docker-compose down
	@echo "Starting PostgreSQL container..."
	docker-compose up -d postgres
	sleep 5 # Wait for PostgreSQL to start
	@echo "Dropping and recreating the database..."
	docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS agentex;"
	docker-compose exec postgres psql -U postgres -c "CREATE DATABASE agentex;"
	@echo "Database reset completed."


# Command to run in production mode
prod:
	ENV=production cargo run

# Command to test (just an example)
test:
	poetry run pytest --cov=agentex
