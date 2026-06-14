#!/bin/sh
set -eu

: "${POSTGRES_HOST:=postgres}"
: "${MAIL_DB_USER:=mail}"
: "${MAIL_DB_PASSWORD:?MAIL_DB_PASSWORD required}"
: "${POSTGRES_DB:=mail}"
: "${MAIL_DOMAIN:=km0digital.com}"

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
render_sql /etc/dovecot/dovecot-sql.conf.ext.template /etc/dovecot/dovecot-sql.conf.ext

if [ ! -f /run/dovecot/ssl/dovecot.pem ] || [ ! -f /run/dovecot/ssl/dovecot.key ]; then
    openssl req -new -x509 -days 3650 -nodes \
        -subj "/CN=${MAIL_DOMAIN}" \
        -keyout /run/dovecot/ssl/dovecot.key \
        -out /run/dovecot/ssl/dovecot.pem
    chmod 600 /run/dovecot/ssl/dovecot.key
fi

chown -R vmail:vmail /var/mail/vhosts

exec "$@"
