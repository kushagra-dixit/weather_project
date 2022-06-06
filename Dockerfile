FROM python:3.9.1-buster

# Setup the working folder
WORKDIR /usr/src/project

# Get the environment type from docker build argument
ARG WORK_ENV="production" 
ENV WORK_ENV=${WORK_ENV} 

# Flask env variables
ENV FLASK_ENV=${WORK_ENV}

# Update the PATH. Required for some python libraries.
ENV PATH="/usr/src/project/.local/bin:${PATH}"

# Dependency manager version (this has to be the same as in pyproject.toml and gitlab-ci.yml)
ENV POETRY_VERSION=1.1.4

# Start using bash instead of sh
SHELL ["/bin/bash", "-c"]

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Poetry dependency manager
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Install project dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install $(test "$WORK_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

# Port
EXPOSE 9999

# Copy the project files into the docker image (add files to the .dockerignore file in order to exlcude them from this copy)
COPY . ./

# Start the API
CMD ["gunicorn", "-c", "gunicorn.conf.py", "service.app:app"]