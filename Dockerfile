# Use the official Docker Hub Ubuntu base image
FROM ubuntu:24.04

# Prevent needing to configure debian packages, stopping the setup of
# the docker container.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Install poetry and any other dependency that your worker needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-poetry \
    wget \
    unzip \
    apt-transport-https \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Update repository to add dotnet
RUN add-apt-repository ppa:dotnet/backports

RUN apt-get update \
    && apt-get install -y --no-install-recommends aspnetcore-runtime-9.0 \
    # Add your dependencies here
    && rm -rf /var/lib/apt/lists/*

# Configure poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set working directory
WORKDIR /openrelik

# Copy project files
COPY . ./

# Install the worker and set environment to use the correct python interpreter.
RUN poetry install && rm -rf $POETRY_CACHE_DIR
ENV VIRTUAL_ENV=/app/.venv PATH="/openrelik/.venv/bin:$PATH"

# ----------------------------------------------------------------------
# Install MFTECmd
# ----------------------------------------------------------------------
ENV MFTECMD_ZIP="MFTECmd.zip"

# Install .net 9 as Linux compatible
# Download the specified Hayabusa release using curl
RUN wget https://download.ericzimmermanstools.com/net9/MFTECmd.zip -O ${MFTECMD_ZIP} --no-check-certificate
# Unzip and clean up
RUN unzip ${MFTECMD_ZIP} -d /mftecmd && rm ${MFTECMD_ZIP}

# extracts contents to
# /mftecmd/MFTECmd.dll
# /mftecmd/MFTECmd.exe
# /mftecmd/MFTECmd.runtimeconfig.json

# ----------------------------------------------------------------------

# Default command if not run from docker-compose (and command being overidden)
CMD ["celery", "--app=openrelik_worker_mftecmd.tasks", "worker", "--task-events", "--concurrency=1", "--loglevel=INFO"]