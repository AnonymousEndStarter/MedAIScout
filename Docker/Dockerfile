FROM ubuntu:22.04
#FROM ultrafunk/undetected-chromedriver:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY ./Docker/requirements.txt .

RUN pip3 install -r requirements.txt

