#!/usr/bin/env python3
"""Localhost-only mailbox provisioning API (register hook + OAuth auto-provision)."""

import json
import logging
import os
import re
import secrets
import subprocess
from pathlib import Path

import bcrypt
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("mail-provision-api")

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN", "km0digital.com")
API_TOKEN = os.environ.get("MAIL_PROVISION_API_TOKEN", "")
LISTEN_PORT = int(os.environ.get("PORT", "8092"))
MAIL_DATA_ROOT = Path(os.environ.get("MAIL_DATA_ROOT", "/var/mail/vhosts"))
VMAIL_UID = int(os.environ.get("VMAIL_UID", "5000"))
VMAIL_GID = int(os.environ.get("VMAIL_GID", "5000"))
COMPOSE_PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", "km0-mail")
RELOAD_POSTFIX_MAPS = os.environ.get("RELOAD_POSTFIX_MAPS", "true").lower() in ("1", "true", "yes")

DB = {
    "host": os.environ.get("POSTGRES_HOST", "postgres"),
    "dbname": os.environ.get("POSTGRES_DB", "mail"),
    "user": os.environ.get("MAIL_DB_USER", "mail"),
    "password": os.environ.get("MAIL_DB_PASSWORD", ""),
}


def db_connect():
    return psycopg2.connect(**DB)


def auth_ok() -> bool:
    if not API_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    return secrets.compare_digest(auth[7:], API_TOKEN)


def validate_email(email: str) -> str | None:
    if not email or not EMAIL_RE.match(email):
        return "invalid_email"
    if not email.endswith("@" + MAIL_DOMAIN):
        return "invalid_domain"
    return None


def hash_password(plain: str) -> str:
    hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()
    if hashed.startswith("$2b$"):
        hashed = "$2y$" + hashed[4:]
    return "{BLF-CRYPT}" + hashed


def ensure_maildir(email: str) -> None:
    local, domain = email.split("@", 1)
    maildir = MAIL_DATA_ROOT / domain / local
    for sub in ("cur", "new", "tmp"):
        (maildir / sub).mkdir(parents=True, exist_ok=True)
    for path in [maildir, maildir / "cur", maildir / "new", maildir / "tmp"]:
        try:
            os.chown(path, VMAIL_UID, VMAIL_GID)
        except PermissionError:
            log.warning("could not chown %s (non-root?)", path)


def reload_postfix_maps() -> None:
    if not RELOAD_POSTFIX_MAPS:
        return
    container = os.environ.get("POSTFIX_CONTAINER", f"{COMPOSE_PROJECT}-postfix-1")
    try:
        subprocess.run(
            ["docker", "exec", container, "build-hash-maps.sh"],
            check=True,
            timeout=60,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.warning("postfix map reload skipped: %s", exc)


def provision_mailbox(email: str, password: str | None, opencloud_uuid: str | None) -> tuple[bool, str]:
    err = validate_email(email)
    if err:
        return False, err

    plain = password or secrets.token_urlsafe(24)
    pw_hash = hash_password(plain)

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mail_accounts (email, password_hash, opencloud_uuid, active)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (email) DO UPDATE SET
                    active = TRUE,
                    opencloud_uuid = COALESCE(EXCLUDED.opencloud_uuid, mail_accounts.opencloud_uuid),
                    updated_at = NOW()
                RETURNING (xmax = 0) AS created
                """,
                (email, pw_hash, opencloud_uuid),
            )
            created = cur.fetchone()[0]
        conn.commit()

    ensure_maildir(email)
    reload_postfix_maps()
    return True, "created" if created else "exists"


@app.route("/health", methods=["GET"])
def health():
    ok = bool(DB["password"])
    return jsonify({"ok": ok, "domain": MAIL_DOMAIN})


@app.route("/provision", methods=["POST"])
def provision():
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401

    if not DB["password"]:
        return jsonify({"error": "service_unavailable"}), 503

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    opencloud_uuid = (data.get("opencloud_uuid") or None)

    ok, status = provision_mailbox(email, password, opencloud_uuid)
    if not ok:
        return jsonify({"error": status}), 400

    code = 201 if status == "created" else 200
    return jsonify({"ok": True, "email": email, "status": status}), code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=LISTEN_PORT)
