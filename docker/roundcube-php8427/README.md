# Roundcube PHP 8.4.27 (PHP2Shell patch)

Built 2026-10-21 on amvara10 for CVE-2026-109618 / CVE-2026-109619.

Hub did not yet publish php:8.4.27 / a Roundcube image with that PHP, so we built locally.

## Images

- php:8.4.27-apache-local — from docker-library/php 8.4/bookworm/apache
- km0-mail-roundcube:1.7.4-php8.4.27 — Roundcube 1.7.4 on that base

## Rebuild

1. Build PHP base from docker-library/php path 8.4/bookworm/apache as tag php:8.4.27-apache-local
2. Build this directory with: docker build --target root --build-arg ROUNDCUBEMAIL_VERSION=1.7.4 -t km0-mail-roundcube:1.7.4-php8.4.27 .
   (MUST use --target root; default nonroot listens on port 8000)
3. cd /opt/km0-mail && docker compose up -d --no-deps --force-recreate roundcube

## Rollback

Restore compose image to roundcube/roundcubemail:1.7.4-apache
(or bak docker-compose.yml.bak.*-php8427) and recreate roundcube.
Previous digest: sha256:08a2af701977785adb02b2a071f6b74787843cd74cf60ce6fcb1d665ef54609b
