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
migration: build-images
	@echo "Starting PostgreSQL container..."
	# Replace with Minikube specific commands if necessary
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -c "DROP DATABASE IF EXISTS agentex;"
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -c "CREATE DATABASE agentex;"

	@echo "Running Alembic migrations..."
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app=agentex-backend -o jsonpath='{.items[0].metadata.name}') -- alembic upgrade head

	@echo "Generating new migration..."
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is not defined. Please provide a name for the migration."; \
		exit 1; \
	fi; \
	minikube kubectl -- exec -it $(shell kubectl get pods --selector=app=agentex-backend -o jsonpath='{.items[0].metadata.name}') -- alembic revision --autogenerate -m "$(NAME)"
	@echo "Migration generation completed."

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
