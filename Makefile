# Variables:
SHELL := /bin/bash

.DEFAULT_GOAL := build

SCRIPTS_DIR_PATH := ./scripts

ifdef NETWORK
NETWORK_ARG = --network $(NETWORK)
endif

ifdef DEBUG
DEBUG_ARG = python -u debug.py
endif

## Colors
INFO_COLOR=\033[0;34m
OK_COLOR=\033[0;32m
WARNING_COLOR=\033[0;33m
ERROR_COLOR=\033[0;31m
NO_COLOR=\033[0m

SERVICE_NAME := weather_project
PORT := 9999
DEBUG_PORT := 8999

# Commands:
build:
	@echo -e "\n${INFO_COLOR}Building $(SERVICE_NAME):${NO_COLOR}\n"
	@DOCKER_BUILDKIT=1 docker build --tag $(SERVICE_NAME) .

start:
	@echo -e "\n${INFO_COLOR}Running $(SERVICE_NAME):${NO_COLOR}\n"
	@docker run \
		$(NETWORK_ARG) \
		-p $(PORT):$(PORT) \
		-p $(DEBUG_PORT):$(DEBUG_PORT) \
		--name $(SERVICE_NAME) \
		-d $(SERVICE_NAME) \
		$(DEBUG_ARG)

stop:
	@echo -e "\n${INFO_COLOR}Stopping $(SERVICE_NAME):${NO_COLOR}\n"
	@docker stop $(SERVICE_NAME) && docker rm -f $(SERVICE_NAME)

dev:
	@echo -e "\n${INFO_COLOR}Building $(SERVICE_NAME):${NO_COLOR}\n"
	@DOCKER_BUILDKIT=1 docker build --build-arg WORK_ENV=development --tag $(SERVICE_NAME) . 
	@make start
	@echo -e "\n${INFO_COLOR}Logs:${NO_COLOR}\n"
	@make logs

lint:
	@poetry run black . --check
	@poetry run flake8 .
	@poetry run bandit . -c .bandit.yml --recursive --quiet

lint-fix:
	@poetry run black .

test: 
	@poetry run pytest --cov=service --cov-report="term" --cov-report="html" -ra

coverage: 
	@poetry run coverage report

logs:
	@docker logs $(SERVICE_NAME) -f

clean:
	@echo -e "\n${INFO_COLOR}Files and folders deleted:${NO_COLOR}"
	@find . \( -name "*.egg*" \) -print -exec rm -rf {} +
	@find . \( -name "__pycache__" \) -print -exec rm -rf {} +
	@find . \( -name ".mypy_cache" \) -print -exec rm -rf {} +
	@find . \( -name ".pytest_cache" \) -print -exec rm -rf {} +
	@find . \( -name ".coverage*" \) -print -exec rm -rf {} +
	@find . \( -name "coverage.html" \) -print -exec rm -rf {} +

docker-rm:
	@echo -e "\n${INFO_COLOR}Removing the docker container...${NO_COLOR}\n"
	@docker rm -f -v $(SERVICE_NAME)

docker-clean:
	@docker system prune -f --filter "label=name=$(SERVICE_NAME)"

pre-push:
	@echo -e "\n${INFO_COLOR}Running a pre-push hook...${NO_COLOR}\n"
	@make lint
	@echo -e "\n${OK_COLOR}Done!${NO_COLOR}\n"

deploy:
	@echo -e "\n${INFO_COLOR}Deploying application to ${WARNING_COLOR}${DEPLOYMENT_ENV}${INFO_COLOR} Cloud Run...${NO_COLOR}\n"
	@gcloud builds submit --tag gcr.io/city-weather-351602/${SERVICE_NAME}
	@gcloud run deploy weather-project \
     --image gcr.io/city-weather-351602/${SERVICE_NAME} \
     --platform managed \
     --region northamerica-northeast1 \
     --allow-unauthenticated \
     --port=${PORT} \
     --set-env-vars "GCLOUD_PROJECT=city-weather-351602" \
     --set-env-vars "PROCESS_RESULT_TOPIC=process_results" \
     --set-env-vars "DATA_LAKE_BUCKET=climate-bucket-111" \
     --set-env-vars "CITIES_DATASET=cities.csv" \
     --set-env-vars "CLIMATE_DATASET=climate.csv" \
	 --set-env-vars "RESULTS_DATASET=results.csv" \
     --set-env-vars "LOCAL_RUN=False"

