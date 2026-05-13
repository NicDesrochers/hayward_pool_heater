FROM ghcr.io/esphome/esphome:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        chromium \
        ninja-build \
        pkg-config \
        tk \
        qemu-system-misc \
        qemu-utils \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir playwright
