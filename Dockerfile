FROM python:3-slim

RUN mkdir -p /app

COPY requirements.txt /app
RUN pip3 install --upgrade pip && pip3 install -r /app/requirements.txt

COPY ./ipytv /app/ipytv
COPY ./tests /app/tests
COPY ./scripts /app/scripts

RUN ln -s /app/scripts/test.sh /usr/bin/runtest && \
    ln -s /app/scripts/lint.sh /usr/bin/runlint

WORKDIR /app/ipytv
ENTRYPOINT [ "/app/scripts/test.sh" ]
