FROM python:3.12-alpine

RUN addgroup -S -g 10001 hermes \
    && adduser -S -D -H -u 10001 -G hermes hermes

USER 10001:10001
WORKDIR /runner

CMD ["python", "--version"]
