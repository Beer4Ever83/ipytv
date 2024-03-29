FROM python:3.9-slim

RUN mkdir -p /app

COPY requirements*.txt /app/
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt && \
    pip install -r /app/requirements-test.txt
COPY ./ipytv /app/ipytv
COPY ./tests /app/tests
COPY ./scripts /app/scripts

RUN ln -s /app/scripts/test.sh /usr/bin/runtest && \
    ln -s /app/scripts/lint.sh /usr/bin/runlint

WORKDIR /app/ipytv
ENTRYPOINT [ "/app/scripts/test.sh" ]
