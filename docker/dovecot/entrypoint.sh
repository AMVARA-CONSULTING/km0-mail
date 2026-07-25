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

# CE 2.4+ ships oauth2 in-core; do not call doveconf here (auth-local.conf
# is not written yet and !include would fail). Older images may ship .so.
has_oauth2_support() {
    case "$(dovecot --version 2>/dev/null)" in
        2.[4-9]*|[3-9].*) return 0 ;;
    esac
    find /usr/lib -name 'libdriver_oauth2.so' 2>/dev/null | grep -q .
}

render_oauth2_block() {
    src="$1"
    sed \
        -e "s|@DEX_INTROSPECTION_URL@|${DEX_INTROSPECTION_URL}|g" \
        -e "s|@DOVECOT_OAUTH_CLIENT_ID@|${DOVECOT_OAUTH_CLIENT_ID}|g" \
        -e "s|@DOVECOT_OAUTH_CLIENT_SECRET@|${DOVECOT_OAUTH_CLIENT_SECRET}|g" \
        "$src"
}

render_auth_local() {
    dest="/run/dovecot/auth-local.conf"
    use_oauth2=0
    if [ -n "${DOVECOT_OAUTH_CLIENT_SECRET}" ] && has_oauth2_support; then
        use_oauth2=1
    fi

    {
        if [ "$use_oauth2" -eq 1 ]; then
            echo "dovecot: OAuth2/XOAUTH2 enabled (Dex LDAP SSO)" >&2
            cat <<'EOF'
auth_mechanisms {
  plain = yes
  login = yes
  xoauth2 = yes
  oauthbearer = yes
}
EOF
            if [ -f /etc/dovecot/dovecot-oauth2.conf.ext.template ]; then
                render_oauth2_block /etc/dovecot/dovecot-oauth2.conf.ext.template
            fi
        else
            if [ -n "${DOVECOT_OAUTH_CLIENT_SECRET}" ] && ! has_oauth2_support; then
                echo "dovecot: DOVECOT_OAUTH_CLIENT_SECRET set but oauth2 support missing — password login only" >&2
            else
                echo "dovecot: OAuth2 disabled — password login only" >&2
            fi
            cat <<'EOF'
auth_mechanisms {
  plain = yes
  login = yes
}
EOF
        fi

        cat <<EOF
sql_driver = pgsql
pgsql ${POSTGRES_HOST} {
  parameters {
    user = ${MAIL_DB_USER}
    password = ${MAIL_DB_PASSWORD}
    dbname = ${POSTGRES_DB}
  }
}

passdb sql {
  mechanisms_filter {
    plain = yes
    login = yes
  }
  default_password_scheme = BLF-CRYPT
  query = SELECT email AS user, password_hash AS password FROM mail_accounts WHERE email='%{user}' AND active=TRUE
}

userdb sql {
  query = SELECT '/var/mail/vhosts/' || split_part(email,'@',2) || '/' || split_part(email,'@',1) AS home, 5000 AS uid, 5000 AS gid FROM mail_accounts WHERE email='%{user}' AND active=TRUE
}
EOF
    } > "$dest"
}

mkdir -p /run/dovecot/ssl /var/mail/vhosts
render_auth_local

if [ ! -f /run/dovecot/ssl/dovecot.pem ] || [ ! -f /run/dovecot/ssl/dovecot.key ]; then
    openssl req -new -x509 -days 3650 -nodes \
        -subj "/CN=${MAIL_DOMAIN}" \
        -keyout /run/dovecot/ssl/dovecot.key \
        -out /run/dovecot/ssl/dovecot.pem
    chmod 600 /run/dovecot/ssl/dovecot.key
fi

chown -R vmail:vmail /var/mail/vhosts

# Fail fast if config is invalid (avoids opaque restart loops)
doveconf -n >/dev/null

exec "$@"
