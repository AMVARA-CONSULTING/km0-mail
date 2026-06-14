FROM debian:bookworm-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        postfix \
        postfix-pgsql \
        postgresql-client \
        libsasl2-modules \
        ca-certificates \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
COPY build-hash-maps.sh /usr/local/bin/build-hash-maps.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/build-hash-maps.sh

EXPOSE 25 587

ENTRYPOINT ["/entrypoint.sh"]
CMD ["postfix", "start-fg"]
