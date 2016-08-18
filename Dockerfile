FROM alpine

MAINTAINER ssteiner@juniper.net

ADD requirements.txt /var/tmp/pyez/requirements.txt

ADD setup.py /var/tmp/pyez/setup.py

WORKDIR /var/tmp/pyez/

RUN apk update \
    && apk upgrade \
    && apk add build-base gcc g++ make python-dev py-pip py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    && pip install -r requirements.txt

RUN sh ./env-setup.sh

RUN python ./setup.py    

RUN apk del -r --purge gcc make g++ \
    && rm -rf /var/cache/apk/*
