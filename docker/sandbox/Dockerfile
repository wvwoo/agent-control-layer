FROM python:3.12-alpine

RUN addgroup -S -g 10001 agentctl \
    && adduser -S -D -H -u 10001 -G agentctl agentctl

USER 10001:10001
WORKDIR /runner

CMD ["python", "--version"]
