#!/bin/sh
set -eu

: "${MAIL_HOSTNAME:=mail.km0digital.com}"
: "${MAIL_DOMAIN:=km0digital.com}"
: "${POSTGRES_HOST:=postgres}"
: "${MAIL_DB_USER:=mail}"
: "${MAIL_DB_PASSWORD:?MAIL_DB_PASSWORD required}"
: "${POSTGRES_DB:=mail}"

render_map() {
    src="$1"
    dest="$2"
    sed \
        -e "s|@POSTGRES_HOST@|${POSTGRES_HOST}|g" \
        -e "s|@MAIL_DB_USER@|${MAIL_DB_USER}|g" \
        -e "s|@MAIL_DB_PASSWORD@|${MAIL_DB_PASSWORD}|g" \
        -e "s|@POSTGRES_DB@|${POSTGRES_DB}|g" \
        "$src" > "$dest"
}

cp /etc/postfix-templates/main.cf /etc/postfix/main.cf

mkdir -p /etc/postfix/sql
for f in /etc/postfix/sql-templates/*.cf; do
    base=$(basename "$f")
    render_map "$f" "/etc/postfix/sql/${base}"
done

/usr/local/bin/build-hash-maps.sh

# Chrooted Postfix processes need host resolver files for LMTP/SASL lookups.
mkdir -p /var/spool/postfix/etc
for f in hosts resolv.conf nsswitch.conf services; do
    if [ -f "/etc/${f}" ]; then
        cp "/etc/${f}" "/var/spool/postfix/etc/${f}"
    fi
done

postconf -e "myhostname = ${MAIL_HOSTNAME}"
postconf -e "mydomain = ${MAIL_DOMAIN}"
postconf -e "myorigin = \$mydomain"
postconf -e "mydestination ="
postconf -e "local_recipient_maps ="
postconf -e "relay_domains ="
postconf -e "virtual_mailbox_domains = hash:/etc/postfix/virtual-mailbox-domains"
postconf -e "virtual_mailbox_maps = hash:/etc/postfix/virtual-mailbox-maps"
postconf -e "virtual_alias_maps = hash:/etc/postfix/virtual-alias-maps"
postconf -e "virtual_transport = lmtp:inet:dovecot:24"
postconf -e "inet_protocols = ipv4"
postconf -e "smtpd_milters = inet:rspamd:11332"
postconf -e "non_smtpd_milters = inet:rspamd:11332"
postconf -e "milter_default_action = accept"
postconf -e "milter_protocol = 6"
postconf -e "smtpd_sasl_type = dovecot"
postconf -e "smtpd_sasl_path = inet:dovecot:12345"
postconf -e "smtpd_sasl_auth_enable = yes"
postconf -e "smtpd_sasl_security_options = noanonymous"
postconf -e "smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, defer_unauth_destination"
postconf -e "smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination"
postconf -e "smtpd_tls_security_level = may"
postconf -e "smtp_tls_security_level = may"
postconf -e "smtpd_tls_cert_file = /etc/ssl/certs/ssl-cert-snakeoil.pem"
postconf -e "smtpd_tls_key_file = /etc/ssl/private/ssl-cert-snakeoil.key"
postconf -e "mynetworks = 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, [::1]/128"

exec "$@"
