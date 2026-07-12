#!/bin/sh
set -eu

: "${POSTGRES_HOST:=postgres}"
: "${MAIL_DB_USER:=mail}"
: "${MAIL_DB_PASSWORD:?MAIL_DB_PASSWORD required}"
: "${POSTGRES_DB:=mail}"
: "${MAIL_DOMAIN:=km0digital.com}"
: "${DEX_INTROSPECTION_URL:=https://cloud.km0digital.com/dex/token/introspect}"
: "${DOVECOT_OAUTH_CLIENT_ID:=km0-mail-dovecot}"
: "${DOVECOT_OAUTH_CLIENT_SECRET:=}"

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

render_oauth2() {
    src="$1"
    dest="$2"
    sed \
        -e "s|@DEX_INTROSPECTION_URL@|${DEX_INTROSPECTION_URL}|g" \
        -e "s|@DOVECOT_OAUTH_CLIENT_ID@|${DOVECOT_OAUTH_CLIENT_ID}|g" \
        -e "s|@DOVECOT_OAUTH_CLIENT_SECRET@|${DOVECOT_OAUTH_CLIENT_SECRET}|g" \
        "$src" > "$dest"
}

has_oauth2_driver() {
    find /usr/lib/dovecot -name 'libdriver_oauth2.so' 2>/dev/null | grep -q .
}

render_auth_conf() {
    dest="/run/dovecot/auth.conf"
    use_oauth2=0
    if [ -n "${DOVECOT_OAUTH_CLIENT_SECRET}" ] && has_oauth2_driver; then
        use_oauth2=1
    fi

    if [ "$use_oauth2" -eq 1 ]; then
        echo "dovecot: OAuth2 passdb enabled (Dex LDAP SSO)" >&2
        cat > "$dest" <<'EOF'
auth_mechanisms = plain login xoauth2 oauthbearer

passdb {
  driver = oauth2
  args = /run/dovecot/dovecot-oauth2.conf.ext
  mechanisms = xoauth2 oauthbearer
}

passdb {
  driver = sql
  args = /run/dovecot/dovecot-sql.conf.ext
  mechanisms = plain login
}
EOF
    else
        if [ -n "${DOVECOT_OAUTH_CLIENT_SECRET}" ] && ! has_oauth2_driver; then
            echo "dovecot: DOVECOT_OAUTH_CLIENT_SECRET set but oauth2 driver missing — password login only" >&2
        else
            echo "dovecot: OAuth2 passdb disabled — password login only" >&2
        fi
        cat > "$dest" <<'EOF'
auth_mechanisms = plain login

passdb {
  driver = sql
  args = /run/dovecot/dovecot-sql.conf.ext
}
EOF
    fi
}

mkdir -p /run/dovecot/ssl /var/mail/vhosts
render_sql /etc/dovecot/dovecot-sql.conf.ext.template /run/dovecot/dovecot-sql.conf.ext
if [ -f /etc/dovecot/dovecot-oauth2.conf.ext.template ] && [ -n "${DOVECOT_OAUTH_CLIENT_SECRET}" ] && has_oauth2_driver; then
    render_oauth2 /etc/dovecot/dovecot-oauth2.conf.ext.template /run/dovecot/dovecot-oauth2.conf.ext
fi
render_auth_conf

if [ ! -f /run/dovecot/ssl/dovecot.pem ] || [ ! -f /run/dovecot/ssl/dovecot.key ]; then
    openssl req -new -x509 -days 3650 -nodes \
        -subj "/CN=${MAIL_DOMAIN}" \
        -keyout /run/dovecot/ssl/dovecot.key \
        -out /run/dovecot/ssl/dovecot.pem
    chmod 600 /run/dovecot/ssl/dovecot.key
fi

chown -R vmail:vmail /var/mail/vhosts

exec "$@"
