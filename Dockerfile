FROM alpine:3.12

LABEL net.juniper.description="Junos PyEZ library for Python in a lightweight container." \
      net.juniper.maintainer="Stephen Steiner <ssteiner@juniper.net>"

WORKDIR /source

## Copy project inside the container
ADD setup.* ./
ADD versioneer.py .
ADD requirements.txt .
ADD lib lib 
ADD entrypoint.sh /usr/local/bin/.

## Install dependancies and PyEZ
RUN apk add --no-cache build-base python3-dev py-lxml \
    libxslt-dev libxml2-dev libffi-dev openssl-dev curl \
    ca-certificates py3-pip bash \
    && pip install -U pip \
    && pip install -r requirements.txt \
    && apk del -r --purge gcc make g++ \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && pip install . \
    && rm -rf /source/* \
    && chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /scripts

VOLUME /scripts

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
