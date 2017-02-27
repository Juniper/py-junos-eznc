FROM alpine:3.4

MAINTAINER ssteiner@juniper.net

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
    && apk add build-base gcc g++ make python-dev py-pip py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    ca-certificates openssl wget \
    && update-ca-certificates \
    && pip install -r requirements.txt \
    && apk del -r --purge gcc make g++ \
    && python setup.py install \
    && rm -rf /source/* \
    && rm -rf /var/cache/apk/*

WORKDIR /scripts

VOLUME ["$PWD:/scripts"]

CMD sh
