#!/bin/sh
# Reload KM0 mail TLS consumers after certbot renews mail.km0digital.com.
# Directory mounts follow the new live/ symlinks; a reload is enough (no volume wipe).
set -eu
if [ "${RENEWED_LINEAGE:-}" != "/etc/letsencrypt/live/mail.km0digital.com" ]; then
    exit 0
fi
docker exec km0-mail-dovecot-1 doveadm reload
docker exec km0-mail-postfix-1 postfix reload
