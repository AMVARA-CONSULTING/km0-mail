FROM debian:bookworm-slim

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        dovecot-core \
        dovecot-imapd \
        dovecot-lmtpd \
        dovecot-pgsql \
        openssl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 5000 vmail \
    && useradd -u 5000 -g vmail -d /var/mail/vhosts -s /usr/sbin/nologin vmail \
    && mkdir -p /var/mail/vhosts /run/dovecot/ssl \
    && chown vmail:vmail /var/mail/vhosts

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 24 993 12345

ENTRYPOINT ["/entrypoint.sh"]
CMD ["dovecot", "-F"]
