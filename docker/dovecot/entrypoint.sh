#!/bin/sh
set -eu

: "${POSTGRES_HOST:=postgres}"
: "${MAIL_DB_USER:=mail}"
: "${MAIL_DB_PASSWORD:?MAIL_DB_PASSWORD required}"
: "${POSTGRES_DB:=mail}"
: "${MAIL_DOMAIN:=km0digital.com}"
: "${DEX_INTROSPECTION_URL:=https://sso.km0digital.com/realms/km0digital/protocol/openid-connect/token/introspect}"
: "${DOVECOT_OAUTH_CLIENT_ID:=km0-mail-web}"
: "${DOVECOT_OAUTH_CLIENT_SECRET:=}"
: "${KEYCLOAK_TOKEN_URL:=https://sso.km0digital.com/realms/km0digital/protocol/openid-connect/token}"

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
            echo "dovecot: OAuth2/XOAUTH2 enabled (Keycloak)" >&2
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

passdb pam {
  mechanisms_filter {
    plain = yes
    login = yes
  }
  service_name = km0-keycloak
  session = no
  setcred = no
}

userdb sql {
  query = SELECT '/var/mail/vhosts/' || split_part(email,'@',2) || '/' || split_part(email,'@',1) AS home, 5000 AS uid, 5000 AS gid FROM mail_accounts WHERE email='%{user}' AND active=TRUE
}
EOF
    } > "$dest"
}

mkdir -p /run/dovecot/ssl /var/mail/vhosts

# Password check for IMAP/SMTP. The script reads the secret from a root-only
# file so it is not stored in the mail database. Mailbox hashes stay in SQL
# unused, for rollback.
umask 077
cat > /run/dovecot/kc-pam.env << EOF
TOKEN_URL=${KEYCLOAK_TOKEN_URL}
INTROSPECT_URL=https://sso.km0digital.com/realms/km0digital/protocol/openid-connect/token/introspect
CLIENT_ID=${DOVECOT_OAUTH_CLIENT_ID}
CLIENT_SECRET=${DOVECOT_OAUTH_CLIENT_SECRET}
EOF
cat > /run/dovecot/kc-pam-auth.sh << 'EOF'
#!/bin/sh
set -a
. /run/dovecot/kc-pam.env
set +a
read -r PASS || true
[ -n "$PASS" ] || exit 1
body=$(curl -sS --max-time 15 -w '\n%{http_code}' \
  -X POST "$TOKEN_URL" \
  --data-urlencode "grant_type=password" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "client_secret=$CLIENT_SECRET" \
  --data-urlencode "scope=openid profile roles" \
  --data-urlencode "username=$PAM_USER" \
  --data-urlencode "password=$PASS") || exit 1
code=$(printf '%s\n' "$body" | tail -n 1)
[ "$code" = "200" ] || exit 1
payload=$(printf '%s\n' "$body" | sed '$d' | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p' | cut -d. -f2)
case $((${#payload} % 4)) in
  2) payload="${payload}==" ;;
  3) payload="${payload}=" ;;
esac
printf '%s' "$payload" | tr '_-' '/+' | base64 -d 2>/dev/null | grep -q '"km0MailUser"'
EOF
chmod 700 /run/dovecot/kc-pam.env /run/dovecot/kc-pam-auth.sh
cat > /etc/pam.d/km0-keycloak << 'EOF'
auth required pam_exec.so quiet expose_authtok /run/dovecot/kc-pam-auth.sh
account required pam_permit.so
EOF

cat > /run/dovecot/kc-introspect.pl << 'EOF'
use strict;
use IO::Socket::INET;
my $id = $ENV{CLIENT_ID} or die "CLIENT_ID missing\n";
my $secret = $ENV{CLIENT_SECRET} or die "CLIENT_SECRET missing\n";
my $url = $ENV{INTROSPECT_URL} or die "INTROSPECT_URL missing\n";
my $srv = IO::Socket::INET->new(
    LocalAddr => "127.0.0.1",
    LocalPort => 8765,
    Proto => "tcp",
    Listen => 20,
    Reuse => 1,
) or die "listen: $!\n";
print STDERR "dovecot: Keycloak introspection proxy ready\n";
while (my $client = $srv->accept()) {
    $client->autoflush(1);
    my $buf = "";
    while ($buf !~ /\r\n\r\n/ && length($buf) < 65536) {
        my $n = sysread($client, my $chunk, 4096);
        last if !$n;
        $buf .= $chunk;
    }
    my ($hdr, $body) = split(/\r\n\r\n/, $buf, 2);
    $body = "" unless defined $body;
    my $len = ($hdr =~ /Content-Length:\s*(\d+)/i) ? $1 : 0;
    while (length($body) < $len && length($body) < 65536) {
        my $n = sysread($client, my $chunk, $len - length($body));
        last if !$n;
        $body .= $chunk;
    }
    my $tmp = "/run/dovecot/intro-body.$$";
    open my $fh, ">", $tmp or die "tmp: $!\n";
    print $fh $body;
    close $fh;
    my $out = `curl -sS --max-time 10 -u '$id:$secret' -H 'Content-Type: application/x-www-form-urlencoded' --data-binary \@$tmp '$url'`;
    unlink $tmp;
    my $status = $? == 0 && length($out) ? "200 OK" : "502 Bad Gateway";
    print $client "HTTP/1.0 $status\r\nContent-Type: application/json\r\nContent-Length: " . length($out) . "\r\nConnection: close\r\n\r\n$out";
    close $client;
}
EOF
chmod 700 /run/dovecot/kc-introspect.pl
set -a
. /run/dovecot/kc-pam.env
set +a
perl /run/dovecot/kc-introspect.pl &

render_auth_local

# Prefer the host Let's Encrypt cert (live + archive are bind-mounted).
# Fall back to a self-signed cert only when those files are absent (local dev).
LE_CERT=/etc/letsencrypt/live/mail.km0digital.com/fullchain.pem
LE_KEY=/etc/letsencrypt/live/mail.km0digital.com/privkey.pem
if [ -f "$LE_CERT" ] && [ -f "$LE_KEY" ]; then
    ln -sfn "$LE_CERT" /run/dovecot/ssl/dovecot.pem
    ln -sfn "$LE_KEY" /run/dovecot/ssl/dovecot.key
elif [ ! -f /run/dovecot/ssl/dovecot.pem ] || [ ! -f /run/dovecot/ssl/dovecot.key ]; then
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
