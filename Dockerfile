FROM python:3-alpine

RUN mkdir -p /app

RUN apk add build-base bash
COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt

COPY ipytv /app/ipytv
COPY ./scripts /app/scripts

RUN ln -s /app/scripts/app.sh /usr/bin/myapp && \
    ln -s /app/scripts/test.sh /usr/bin/mytest

WORKDIR /app/webcrawler
ENTRYPOINT [ "/app/scripts/app.sh" ]
