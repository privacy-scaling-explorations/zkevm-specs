help: ## Display this help screen
	@grep -h \
		-E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: # Install the Python packages
	poetry update

fmt: ## Format the code
	poetry run black .

lint: ## Check whether the code is formated correctly
	poetry run black . --check

type: ## Check whether the typing of the Python code
	poetry run mypy zkevm_specs

test: ## Run tests
	poetry run pytest


.PHONY: help install fmt lint test
