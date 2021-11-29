help: ## Display this help screen
	@grep -h \
		-E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: # Install the Python packages
	pip3 install .[test,lint]

fmt: ## Format the code
	black .
	mdformat . --number

lint: ## Check whether the code is formated correctly
	black . --check
	mdformat . --number --check

test: ## Run tests
	pytest


.PHONY: help install fmt lint test
