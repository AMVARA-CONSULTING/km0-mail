# Roundcube PHP 8.4.27 (PHP2Shell patch)

Built 2026-10-21 on amvara10 for CVE-2026-109618 / CVE-2026-109619.

Hub did not yet publish php:8.4.27 / a Roundcube image with that PHP, so we built locally.

## Images

- php:8.4.27-apache-local — from docker-library/php 8.4/bookworm/apache
- km0-mail-roundcube:1.7.5-php8.4.27 — Roundcube 1.7.5 on that base (was 1.7.4)

## Rebuild

1. Build PHP base from docker-library/php path 8.4/bookworm/apache as tag php:8.4.27-apache-local
2. Build this directory with: docker build --target root --build-arg ROUNDCUBEMAIL_VERSION=1.7.5 -t km0-mail-roundcube:1.7.5-php8.4.27 .
   (MUST use --target root; default nonroot listens on port 8000)
3. cd /opt/km0-mail && docker compose up -d --no-deps --force-recreate roundcube

## Rollback

Restore compose image to `km0-mail-roundcube:1.7.4-php8.4.27` (or stock `roundcube/roundcubemail:1.7.4-apache` / bak `docker-compose.yml.bak.*-php8427`) and recreate roundcube.
Previous 1.7.4-php8.4.27 digest: sha256:053442e089706308f70dfec52948bb94788543fa6b9960731a76eb409b0f6e6b
