FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    pkg-config \
    ninja-build \
    gdb \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work