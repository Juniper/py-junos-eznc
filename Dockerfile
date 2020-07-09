FROM alpine:3.7

LABEL net.juniper.description="Junos PyEZ library for Python in a lightweight container." \
      net.juniper.maintainer="Stephen Steiner <ssteiner@juniper.net>"

WORKDIR /source

## Copy project inside the container
ADD setup.py setup.py
ADD setup.cfg setup.cfg
ADD requirements.txt requirements.txt
ADD lib lib

## Install dependancies and PyEZ
RUN apk add --no-cache build-base python3-dev py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    ca-certificates openssl \
    && pip3 install -U pip \
    && pip3 install -r requirements.txt \
    && apk del -r --purge gcc make g++ \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && pip3 install . \
    && rm -rf /source/*

WORKDIR /scripts

VOLUME /scripts
