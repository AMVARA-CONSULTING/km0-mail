FROM debian:bookworm-slim

# Dovecot CE 2.4 from repo.dovecot.org — includes built-in OAuth2/XOAUTH2
# (Debian Bookworm packages are 2.3 and lack oauth2).
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        openssl \
    && curl -fsSL https://repo.dovecot.org/DOVECOT-REPO-GPG-2.4 \
        | gpg --dearmor -o /usr/share/keyrings/dovecot.gpg \
    && printf '%s\n' \
        'Types: deb' \
        'URIs: https://repo.dovecot.org/ce-2.4-latest/debian/bookworm' \
        'Suites: bookworm' \
        'Components: main' \
        'Signed-By: /usr/share/keyrings/dovecot.gpg' \
        > /etc/apt/sources.list.d/dovecot.sources \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        dovecot-core \
        dovecot-imapd \
        dovecot-lmtpd \
        dovecot-pgsql \
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
