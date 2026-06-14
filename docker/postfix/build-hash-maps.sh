#!/bin/sh
# Rebuild Postfix hash maps from PostgreSQL (called at startup and after provisioning).
set -eu

: "${POSTGRES_HOST:=postgres}"
: "${MAIL_DB_USER:=mail}"
: "${MAIL_DB_PASSWORD:?MAIL_DB_PASSWORD required}"
: "${POSTGRES_DB:=mail}"

wait_for_postgres() {
    tries=0
    while [ "$tries" -lt 30 ]; do
        if PGPASSWORD="$MAIL_DB_PASSWORD" psql -h "$POSTGRES_HOST" -U "$MAIL_DB_USER" -d "$POSTGRES_DB" -c 'SELECT 1' >/dev/null 2>&1; then
            return 0
        fi
        tries=$((tries + 1))
        sleep 1
    done
    echo "build-hash-maps: postgres at ${POSTGRES_HOST} not ready" >&2
    return 1
}

wait_for_postgres

PGPASSWORD="$MAIL_DB_PASSWORD" psql -h "$POSTGRES_HOST" -U "$MAIL_DB_USER" -d "$POSTGRES_DB" -At -F '	' -c \
    "SELECT name FROM mail_domains WHERE active=TRUE" \
    | while IFS= read -r domain; do
        [ -n "$domain" ] || continue
        printf '%s\tOK\n' "$domain"
    done > /etc/postfix/virtual-mailbox-domains

PGPASSWORD="$MAIL_DB_PASSWORD" psql -h "$POSTGRES_HOST" -U "$MAIL_DB_USER" -d "$POSTGRES_DB" -At -F '	' -c \
    "SELECT email, CONCAT(SPLIT_PART(email,'@',2),'/',SPLIT_PART(email,'@',1),'/') FROM mail_accounts WHERE active=TRUE" \
    > /etc/postfix/virtual-mailbox-maps

PGPASSWORD="$MAIL_DB_PASSWORD" psql -h "$POSTGRES_HOST" -U "$MAIL_DB_USER" -d "$POSTGRES_DB" -At -F '	' -c \
    "SELECT alias_address, target_email FROM mail_aliases" \
    > /etc/postfix/virtual-alias-maps

postmap /etc/postfix/virtual-mailbox-domains
postmap /etc/postfix/virtual-mailbox-maps
postmap /etc/postfix/virtual-alias-maps
postfix reload 2>/dev/null || true
