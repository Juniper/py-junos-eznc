FROM ubuntu:26.04

LABEL net.juniper.description="Junos PyEZ library for Python in a lightweight container." \
      net.juniper.maintainer="jnpr-community-netdev@juniper.net"

WORKDIR /source

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

## Copy project inside the container
ADD setup.* ./
ADD versioneer.py .
ADD requirements.txt .
ADD lib lib 
ADD entrypoint.sh /usr/local/bin/.

## Install system dependencies, native Python 3.14, and build toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    libxslt1-dev \
    libxml2-dev \
    libffi-dev \
    libssl-dev \
    curl \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/*

## Install pipdeptree, requirements, and PyEZ package using native python3 (skipped pip upgrade)
RUN python3 -m pip install --break-system-packages --no-cache-dir pipdeptree \
    && python3 -m pip install --break-system-packages --no-cache-dir -r requirements.txt \
    && python3 -m pip install --break-system-packages --no-cache-dir .

## Clean up heavy build toolchain packages to minimize image size
RUN apt-get purge -y --auto-remove \
    build-essential \
    python3-dev \
    libxslt1-dev \
    libxml2-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /source/* \
    && chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /scripts

VOLUME /scripts

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
