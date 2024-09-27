# Makefile

install:
	poetry install

# Command to run in development mode
dev:
	ENV=development UVICORN_PORT=5003 uvicorn agentex.api.app:app --reload

# Command to run in production mode
prod:
	ENV=production cargo run

# Command to test (just an example)
test:
	cargo test
