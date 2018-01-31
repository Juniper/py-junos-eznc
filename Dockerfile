FROM alpine:3.6

LABEL MAINTAINER="Stephen Steiner <ssteiner@juniper.net>"

LABEL net.juniper.description="Junos PyEZ library for Python in a lightweight container." \
      net.juniper.maintainer="Stephen Steiner <ssteiner@juniper.net>"

RUN mkdir /source \
    && mkdir /scripts

WORKDIR /source

## Copy project inside the container
ADD setup.py setup.py
ADD requirements.txt requirements.txt
ADD lib lib

## Install dependancies and Pyez
RUN apk update \
    && apk upgrade \
    && apk add build-base python-dev py-pip py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    ca-certificates openssl wget \
    && update-ca-certificates \
    && pip install --upgrade pip setuptools \
    && pip install -r requirements.txt \
    && apk del -r --purge gcc make g++ \
    && python setup.py install \
    && rm -rf /source/* \
    && rm -rf /var/cache/apk/*

WORKDIR /scripts

VOLUME /scripts
