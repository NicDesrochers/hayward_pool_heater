FROM ghcr.io/esphome/esphome:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ninja-build \
        pkg-config \
        qemu-system-misc \
        qemu-utils \
    && rm -rf /var/lib/apt/lists/*
