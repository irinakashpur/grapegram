ARG BASE_IMAGE=python:3.10-slim-buster
FROM $BASE_IMAGE

# system update & package install
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    openssl libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .
WORKDIR .

# pip & requirements
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

# Execute
CMD ["python", "main.py"]
