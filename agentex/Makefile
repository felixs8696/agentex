# Makefile

install:
	poetry install

start-cluster:
	minikube start

stop-cluster:
	minikube stop

k9s:
	k9s

# Set Minikube's Docker environment
minikube-env:
	eval $(minikube -p minikube docker-env)

# Command to build images using Minikube's Docker daemon
build-images: minikube-env
	# Build agentex-backend image
	docker build -f Dockerfile -t agentex-backend:latest .
	# Build temporal-worker image
	docker build -f Dockerfile.temporal.worker -t agentex-worker:latest .

# Command to deploy using Helm and reset Docker environment
deploy: build-images
	helmfile -f charts/helmfile.dev.yaml apply
	eval $(minikube -p minikube docker-env -u)

# Command to run everything in development mode using Minikube
dev: build-images deploy
	kubectl port-forward service/agentex 5003:80

# Command to stop and remove all services
uninstall:
	helm uninstall agentex
	helm uninstall agentex-workers
	helm uninstall redis
	helm uninstall temporal

# Command to create a new Alembic migration
# Command to create a new Alembic migration
migration:
	@echo "Starting PostgreSQL migration process..."

	# Check if a migration name (NAME) is provided
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is not defined. Please provide a name for the migration."; \
		exit 1; \
	fi

	@echo "Running Alembic upgrade to the latest version in the agentex pod..."
	# Upgrade the database schema to the latest version inside the Kubernetes cluster
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app.kubernetes.io/name=agentex -o jsonpath='{.items[0].metadata.name}') -- sh -c "cd /app/database/migrations && alembic upgrade head"

	@echo "Generating a new Alembic migration inside the agentex pod..."
	# Generate the migration inside the pod, using the PostgreSQL database
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app.kubernetes.io/name=agentex -o jsonpath='{.items[0].metadata.name}') -- sh -c "cd /app/database/migrations && alembic revision --autogenerate -m '$(NAME)'"

	@echo "Copying the generated migration file to the local project..."
	# Copy the generated migration file from the pod to your local directory
	POD_MIGRATION_FILE=$$(minikube kubectl -- exec $(shell kubectl get pods --selector=app.kubernetes.io/name=agentex -o jsonpath='{.items[0].metadata.name}') -- sh -c "ls /app/database/migrations/alembic/versions/*.py | sort | tail -n 1"); \
	minikube kubectl cp $(shell kubectl get pods --selector=app.kubernetes.io/name=agentex -o jsonpath='{.items[0].metadata.name}'):/app/database/migrations/alembic/versions/$$POD_MIGRATION_FILE ./database/migrations/alembic/versions/

	@echo "Migration generation completed and copied to the local machine."

clean-db:
	@echo "Dropping and recreating the database..."
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -c "DROP DATABASE IF EXISTS agentex;"
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -c "CREATE DATABASE agentex;"
	@echo "Database reset completed."

# Command to test
test:
	poetry run pytest --cov=agentex

# Reset Docker environment after build (optional)
reset-docker-env:
	eval $(minikube -p minikube docker-env -u)
