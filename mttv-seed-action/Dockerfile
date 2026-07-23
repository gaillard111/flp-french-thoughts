FROM alpine:3.19

RUN apk add --no-cache bash findutils grep

COPY entrypoint.sh /entrypoint.sh
COPY seeds/ /seeds/

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
