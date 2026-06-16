#!/bin/sh
set -eu

: "${POSTGRES_HOST:=postgres}"
: "${MAIL_DB_USER:=mail}"
: "${MAIL_DB_PASSWORD:?MAIL_DB_PASSWORD required}"
: "${POSTGRES_DB:=mail}"
: "${MAIL_DOMAIN:=km0digital.com}"
: "${DEX_INTROSPECTION_URL:=https://cloud.km0digital.com/dex/token/introspect}"
: "${DOVECOT_OAUTH_CLIENT_ID:=km0-mail-dovecot}"
: "${DOVECOT_OAUTH_CLIENT_SECRET:?DOVECOT_OAUTH_CLIENT_SECRET required}"

render_sql() {
    src="$1"
    dest="$2"
    sed \
        -e "s|@POSTGRES_HOST@|${POSTGRES_HOST}|g" \
        -e "s|@MAIL_DB_USER@|${MAIL_DB_USER}|g" \
        -e "s|@MAIL_DB_PASSWORD@|${MAIL_DB_PASSWORD}|g" \
        -e "s|@POSTGRES_DB@|${POSTGRES_DB}|g" \
        "$src" > "$dest"
}

mkdir -p /run/dovecot/ssl /var/mail/vhosts
render_sql /etc/dovecot/dovecot-sql.conf.ext.template /run/dovecot/dovecot-sql.conf.ext

render_oauth() {
    src="$1"
    dest="$2"
    sed \
        -e "s|@DEX_INTROSPECTION_URL@|${DEX_INTROSPECTION_URL}|g" \
        -e "s|@DOVECOT_OAUTH_CLIENT_ID@|${DOVECOT_OAUTH_CLIENT_ID}|g" \
        -e "s|@DOVECOT_OAUTH_CLIENT_SECRET@|${DOVECOT_OAUTH_CLIENT_SECRET}|g" \
        "$src" > "$dest"
}

render_oauth /etc/dovecot/dovecot-oauth2.conf.ext.template /run/dovecot/dovecot-oauth2.conf.ext

if [ ! -f /run/dovecot/ssl/dovecot.pem ] || [ ! -f /run/dovecot/ssl/dovecot.key ]; then
    openssl req -new -x509 -days 3650 -nodes \
        -subj "/CN=${MAIL_DOMAIN}" \
        -keyout /run/dovecot/ssl/dovecot.key \
        -out /run/dovecot/ssl/dovecot.pem
    chmod 600 /run/dovecot/ssl/dovecot.key
fi

chown -R vmail:vmail /var/mail/vhosts

exec "$@"
