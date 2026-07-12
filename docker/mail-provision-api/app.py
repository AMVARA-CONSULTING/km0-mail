#!/usr/bin/env python3
"""Localhost-only mailbox provisioning API (register hook + OAuth auto-provision)."""

import json
import logging
import os
import re
import secrets
import smtplib
import subprocess
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode

import bcrypt
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("mail-provision-api")

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN", "km0digital.com")
MAIL_HOSTNAME = os.environ.get("MAIL_HOSTNAME", "mail.km0digital.com")
API_TOKEN = os.environ.get("MAIL_PROVISION_API_TOKEN", "")
LISTEN_PORT = int(os.environ.get("PORT", "8092"))
MAIL_DATA_ROOT = Path(os.environ.get("MAIL_DATA_ROOT", "/var/mail/vhosts"))
VMAIL_UID = int(os.environ.get("VMAIL_UID", "5000"))
VMAIL_GID = int(os.environ.get("VMAIL_GID", "5000"))
COMPOSE_PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", "km0-mail")
RELOAD_POSTFIX_MAPS = os.environ.get("RELOAD_POSTFIX_MAPS", "true").lower() in ("1", "true", "yes")
SMTP_RELAY = os.environ.get("SMTP_RELAY", "postfix:587")
NOREPLY = os.environ.get("NOREPLY_ADDRESS", f"noreply@{MAIL_DOMAIN}")
VERIFY_BASE_URL = os.environ.get("VERIFY_BASE_URL", f"https://{MAIL_HOSTNAME}/verify")

FREEMAIL_DOMAINS = frozenset(
    d.strip().lower()
    for d in os.environ.get(
        "FREEMAIL_DOMAINS",
        "gmail.com,googlemail.com,outlook.com,hotmail.com,live.com,yahoo.com,"
        "icloud.com,proton.me,protonmail.com,aol.com,gmx.com,mail.com,yandex.com",
    ).split(",")
    if d.strip()
)

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


def domain_of(email: str) -> str:
    return email.split("@", 1)[1].lower()


def is_freemail_domain(domain: str) -> bool:
    return domain.lower() in FREEMAIL_DOMAINS


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


def send_verification_email(email: str, token: str) -> None:
    verify_url = f"{VERIFY_BASE_URL}?{urlencode({'token': token})}"
    msg = EmailMessage()
    msg["From"] = f"KM0 Mail <{NOREPLY}>"
    msg["To"] = email
    msg["Subject"] = "Confirm your KM0 Mail account"
    msg.set_content(
        f"Welcome to KM0 Mail.\n\n"
        f"Open this link to confirm your account and enable sending:\n{verify_url}\n\n"
        f"If you did not register, ignore this message.\n"
    )
    host, port = SMTP_RELAY.split(":")
    with smtplib.SMTP(host, int(port), timeout=30) as smtp:
        smtp.ehlo()
        if smtp.has_extn("starttls"):
            smtp.starttls()
            smtp.ehlo()
        smtp.send_message(msg)


def validate_mailbox_email(email: str, mail_mode: str) -> str | None:
    if not email or not EMAIL_RE.match(email):
        return "invalid_email"
    domain = domain_of(email)
    if mail_mode == "km0":
        if domain != MAIL_DOMAIN:
            return "invalid_domain"
    elif mail_mode == "custom":
        if domain == MAIL_DOMAIN:
            return "invalid_domain"
        if is_freemail_domain(domain):
            return "freemail_blocked"
    else:
        return "invalid_mail_mode"
    return None


def provision_mailbox(
    email: str,
    password: str | None,
    opencloud_uuid: str | None,
    mail_mode: str,
    contact_email: str | None,
    send_verify: bool = True,
) -> tuple[bool, str, dict | None]:
    email = email.strip().lower()
    err = validate_mailbox_email(email, mail_mode)
    if err:
        return False, err, None

    if contact_email and is_freemail_domain(domain_of(contact_email)):
        pass  # contact freemail allowed

    plain = password or secrets.token_urlsafe(24)
    pw_hash = hash_password(plain)
    verify_token = secrets.token_urlsafe(32)
    verification_status = "pending" if mail_mode == "km0" else "pending"
    domain = domain_of(email)

    with db_connect() as conn:
        with conn.cursor() as cur:
            if mail_mode == "custom":
                cur.execute(
                    """
                    INSERT INTO mail_domains (
                        name, active, owner_opencloud_uuid, verification_token,
                        verification_status, mx_verified, spf_verified, dkim_verified, txt_verified
                    ) VALUES (%s, FALSE, %s, %s, 'pending', FALSE, FALSE, FALSE, FALSE)
                    ON CONFLICT (name) DO UPDATE SET
                        owner_opencloud_uuid = COALESCE(EXCLUDED.owner_opencloud_uuid, mail_domains.owner_opencloud_uuid),
                        verification_token = COALESCE(mail_domains.verification_token, EXCLUDED.verification_token)
                    """,
                    (domain, opencloud_uuid, secrets.token_urlsafe(24)),
                )

            cur.execute(
                """
                INSERT INTO mail_accounts (
                    email, password_hash, opencloud_uuid, active,
                    verification_status, verification_token, contact_email, mail_mode
                ) VALUES (%s, %s, %s, TRUE, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = CASE WHEN EXCLUDED.password_hash IS NOT NULL THEN EXCLUDED.password_hash ELSE mail_accounts.password_hash END,
                    active = TRUE,
                    opencloud_uuid = COALESCE(EXCLUDED.opencloud_uuid, mail_accounts.opencloud_uuid),
                    contact_email = COALESCE(EXCLUDED.contact_email, mail_accounts.contact_email),
                    mail_mode = COALESCE(EXCLUDED.mail_mode, mail_accounts.mail_mode),
                    updated_at = NOW()
                RETURNING (xmax = 0) AS created, verification_status, verification_token
                """,
                (email, pw_hash, opencloud_uuid, verification_status, verify_token, contact_email, mail_mode),
            )
            row = cur.fetchone()
            created = row[0]
            current_status = row[1]
            current_token = row[2]
        conn.commit()

    ensure_maildir(email)
    reload_postfix_maps()

    if send_verify and mail_mode == "km0" and current_status == "pending" and current_token:
        try:
            send_verification_email(email, current_token)
        except Exception as exc:
            log.warning("verification email failed for %s: %s", email, exc)

    status = "created" if created else "exists"
    return True, status, {"verification_status": current_status, "mail_mode": mail_mode}


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
    email = (data.get("email") or data.get("desired_email") or "").strip().lower()
    password = data.get("password")
    opencloud_uuid = data.get("opencloud_uuid") or None
    mail_mode = (data.get("mail_mode") or "km0").strip().lower()
    contact_email = (data.get("contact_email") or "").strip().lower() or None
    send_verify = data.get("send_verification", True)

    if mail_mode not in ("km0", "custom"):
        return jsonify({"error": "invalid_mail_mode"}), 400

    ok, status, extra = provision_mailbox(
        email, password, opencloud_uuid, mail_mode, contact_email, send_verify=send_verify
    )
    if not ok:
        return jsonify({"error": status}), 400

    code = 201 if status == "created" else 200
    body = {"ok": True, "email": email, "status": status}
    if extra:
        body.update(extra)
    return jsonify(body), code


@app.route("/update-password", methods=["POST"])
def update_password():
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "missing_fields"}), 400

    pw_hash = hash_password(password)
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mail_accounts SET password_hash=%s, updated_at=NOW() WHERE email=%s AND active=TRUE",
                (pw_hash, email),
            )
            updated = cur.rowcount
        conn.commit()

    if not updated:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"ok": True, "email": email})


@app.route("/account/<path:email>/status", methods=["GET"])
def account_status(email: str):
    email = email.strip().lower()
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT verification_status, mail_mode, active
                FROM mail_accounts WHERE lower(email) = lower(%s)
                """,
                (email,),
            )
            row = cur.fetchone()
    if not row:
        return jsonify({"error": "not_found"}), 404
    return jsonify(
        {
            "email": email,
            "verification_status": row[0],
            "mail_mode": row[1],
            "active": row[2],
        }
    )


@app.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    token = (request.args.get("token") or "").strip()
    if not token and request.is_json:
        data = request.get_json(silent=True) or {}
        token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"error": "missing_token"}), 400

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE mail_accounts
                SET verification_status = 'verified', verification_token = NULL, updated_at = NOW()
                WHERE verification_token = %s AND verification_status = 'pending'
                RETURNING email
                """,
                (token,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        return jsonify({"error": "invalid_or_expired_token"}), 404

    return jsonify({"ok": True, "email": row[0], "verification_status": "verified"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=LISTEN_PORT)
