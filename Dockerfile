FROM alpine:3.4

MAINTAINER ssteiner@juniper.net

WORKDIR /tmp

ADD requirements.txt /tmp/.

RUN apk update \
    && apk upgrade \
    && apk add build-base gcc g++ make python-dev py-pip py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    && pip install -r requirements.txt \
    && apk del -r --purge gcc make g++ \
    && rm -rf /var/cache/apk/* \
    && cd /

