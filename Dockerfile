FROM alpine:3.7

LABEL net.juniper.description="Junos PyEZ library for Python in a lightweight container." \
      net.juniper.maintainer="Stephen Steiner <ssteiner@juniper.net>"

WORKDIR /source

## Copy project inside the container
ADD setup.* ./
#ADD setup.cfg .
ADD versioneer.py .
ADD requirements.txt .
ADD lib lib 

## Install dependancies and PyEZ
RUN apk add --no-cache build-base python3-dev py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    ca-certificates \
    && pip3 install -U pip \
    && pip3 install -r requirements.txt \
    && apk del -r --purge gcc make g++ \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && pip3 install . \
    && rm -rf /source/*

WORKDIR /scripts

VOLUME /scripts
