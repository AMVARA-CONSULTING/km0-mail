#!/usr/bin/env python3
"""Localhost-only mailbox provisioning API (register hook + OAuth auto-provision)."""

import json
import logging
import os
import re
import secrets
import smtplib
import subprocess
import threading
import time
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
LOCAL_PART_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._+-]{0,62}[a-zA-Z0-9])?$")
MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN", "km0digital.com")
MAIL_HOSTNAME = os.environ.get("MAIL_HOSTNAME", "mail.km0digital.com")
AUTH_HUB_URL = os.environ.get("AUTH_HUB_URL", "https://auth.km0digital.com").rstrip("/")
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

# Public /register throttle (per client IP; in-process, dependency-light).
REGISTER_RATE_MAX = int(os.environ.get("REGISTER_RATE_MAX", "10"))
REGISTER_RATE_WINDOW = int(os.environ.get("REGISTER_RATE_WINDOW_SEC", "300"))

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


_rate_lock = threading.Lock()
_rate_hits: dict[str, list[float]] = {}


def client_ip() -> str:
    """Real client IP behind nginx (X-Forwarded-For first hop, then X-Real-IP)."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or request.remote_addr or "unknown"


def rate_limited(ip: str) -> bool:
    """Sliding-window limiter: True once an IP exceeds REGISTER_RATE_MAX in the window."""
    now = time.time()
    with _rate_lock:
        hits = [t for t in _rate_hits.get(ip, []) if now - t < REGISTER_RATE_WINDOW]
        if len(hits) >= REGISTER_RATE_MAX:
            _rate_hits[ip] = hits
            return True
        hits.append(now)
        _rate_hits[ip] = hits
        if len(_rate_hits) > 10000:
            for key in [k for k, v in _rate_hits.items() if all(now - t >= REGISTER_RATE_WINDOW for t in v)]:
                del _rate_hits[key]
    return False


def domain_of(email: str) -> str:
    return email.split("@", 1)[1].lower()


DOMAIN_NAME_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
)


def normalize_domain(domain: str) -> str | None:
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain or not DOMAIN_NAME_RE.match(domain):
        return None
    return domain


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
    # Freemail is never a mailbox (Gmail stays contact_email only).
    if is_freemail_domain(domain):
        return "freemail_blocked"
    if mail_mode == "km0":
        if domain != MAIL_DOMAIN:
            return "invalid_domain"
    elif mail_mode == "custom":
        if domain == MAIL_DOMAIN:
            return "invalid_domain"
    else:
        return "invalid_mail_mode"
    return None


def validate_local_part(local_part: str) -> str | None:
    if not local_part or not LOCAL_PART_RE.match(local_part):
        return "invalid_local_part"
    if ".." in local_part:
        return "invalid_local_part"
    return None


def entry_hints(email: str) -> dict:
    """Post-activate login paths for hub / wizard (no Google IdP on Roundcube)."""
    password_login = (
        f"https://{MAIL_HOSTNAME}/index.php?_task=login&activated=1"
    )
    return {
        "mailbox": email,
        "password_login_url": password_login,
        "hub_url": AUTH_HUB_URL,
        "verify_path": f"https://{MAIL_HOSTNAME}/verify",
        "next_steps": [
            "password_login",
            "open_verification_email_in_inbox",
            "click_verify_link",
            "optional_ldap_oauth",
        ],
        "ldap_oauth": {
            "status": "preferred_after_idm_mail_attr",
            "connector_id": "ldap",
            "note": (
                "Roundcube OAuth uses Dex LDAP only so the token email claim equals "
                f"the mailbox ({email}). Requires IDM mail={email} and Dovecot XOAUTH2 (#9). "
                "Do not use Dex connector_id=google for Roundcube (see spike #12). "
                "Optional after password login + verify; not required for verification."
            ),
        },
        "password_login": {
            "status": "available_immediately",
            "note": (
                "Roundcube native login → Dovecot SQL passdb; works without OAuth/#9. "
                "Required path to read the @km0 verification email (Google IdP cannot open the mailbox)."
            ),
            "url": password_login,
        },
        "google_cloud_idp": {
            "note": (
                "Google remains Cloud IdP only; freemail is contact_email. "
                "Do not use Google for Roundcube or the verify step. "
                "Coordinate opencloud #24 before shipping activate UX that rewrites Graph mail."
            ),
        },
    }


def fetch_account_by_uuid(cur, opencloud_uuid: str) -> dict | None:
    cur.execute(
        """
        SELECT email, opencloud_uuid, contact_email, verification_status, mail_mode, active
        FROM mail_accounts
        WHERE opencloud_uuid = %s
        LIMIT 1
        """,
        (opencloud_uuid,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "email": row[0],
        "opencloud_uuid": row[1],
        "contact_email": row[2],
        "verification_status": row[3],
        "mail_mode": row[4],
        "active": row[5],
    }


def fetch_account_by_contact(cur, contact_email: str) -> list[dict]:
    cur.execute(
        """
        SELECT email, opencloud_uuid, contact_email, verification_status, mail_mode, active
        FROM mail_accounts
        WHERE contact_email IS NOT NULL AND lower(contact_email) = lower(%s)
        ORDER BY id
        """,
        (contact_email,),
    )
    return [
        {
            "email": row[0],
            "opencloud_uuid": row[1],
            "contact_email": row[2],
            "verification_status": row[3],
            "mail_mode": row[4],
            "active": row[5],
        }
        for row in cur.fetchall()
    ]


def account_payload(row: dict) -> dict:
    return {
        "email": row["email"],
        "opencloud_uuid": row.get("opencloud_uuid"),
        "contact_email": row.get("contact_email"),
        "verification_status": row.get("verification_status"),
        "mail_mode": row.get("mail_mode"),
        "active": row.get("active"),
    }


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
            # 1 OpenCloud user = 1 mailbox: same uuid + same email → idempotent;
            # same uuid + different email → conflict.
            if opencloud_uuid:
                existing = fetch_account_by_uuid(cur, opencloud_uuid)
                if existing:
                    if existing["email"] == email:
                        if contact_email and not existing.get("contact_email"):
                            cur.execute(
                                """
                                UPDATE mail_accounts
                                SET contact_email = COALESCE(contact_email, %s),
                                    updated_at = NOW()
                                WHERE email = %s
                                RETURNING verification_status, mail_mode
                                """,
                                (contact_email, email),
                            )
                            upd = cur.fetchone()
                            conn.commit()
                            return True, "exists", {
                                "verification_status": upd[0] if upd else existing["verification_status"],
                                "mail_mode": upd[1] if upd else existing["mail_mode"],
                                "email": email,
                            }
                        return True, "exists", {
                            "verification_status": existing["verification_status"],
                            "mail_mode": existing["mail_mode"] or mail_mode,
                            "email": email,
                        }
                    return False, "uuid_already_linked", {
                        "existing_email": existing["email"],
                        "opencloud_uuid": opencloud_uuid,
                    }

            if mail_mode == "custom":
                cur.execute(
                    """
                    INSERT INTO mail_domains (
                        name, active, owner_opencloud_uuid, owner_email, verification_token,
                        verification_status, mx_verified, spf_verified, dkim_verified, txt_verified
                    ) VALUES (%s, FALSE, %s, %s, %s, 'pending', FALSE, FALSE, FALSE, FALSE)
                    ON CONFLICT (name) DO UPDATE SET
                        owner_opencloud_uuid = COALESCE(EXCLUDED.owner_opencloud_uuid, mail_domains.owner_opencloud_uuid),
                        owner_email = COALESCE(mail_domains.owner_email, EXCLUDED.owner_email),
                        verification_token = COALESCE(mail_domains.verification_token, EXCLUDED.verification_token)
                    """,
                    (domain, opencloud_uuid, email, secrets.token_urlsafe(24)),
                )

            try:
                cur.execute(
                    """
                    INSERT INTO mail_accounts (
                        email, password_hash, opencloud_uuid, active,
                        verification_status, verification_token, contact_email, mail_mode
                    ) VALUES (%s, %s, %s, TRUE, %s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET
                        password_hash = CASE WHEN EXCLUDED.password_hash IS NOT NULL THEN EXCLUDED.password_hash ELSE mail_accounts.password_hash END,
                        active = TRUE,
                        opencloud_uuid = COALESCE(mail_accounts.opencloud_uuid, EXCLUDED.opencloud_uuid),
                        contact_email = COALESCE(EXCLUDED.contact_email, mail_accounts.contact_email),
                        mail_mode = COALESCE(EXCLUDED.mail_mode, mail_accounts.mail_mode),
                        updated_at = NOW()
                    RETURNING (xmax = 0) AS created, verification_status, verification_token, opencloud_uuid
                    """,
                    (email, pw_hash, opencloud_uuid, verification_status, verify_token, contact_email, mail_mode),
                )
                row = cur.fetchone()
            except psycopg2.IntegrityError as exc:
                conn.rollback()
                if opencloud_uuid and "idx_mail_accounts_opencloud_uuid_unique" in str(exc):
                    with db_connect() as conn2:
                        with conn2.cursor() as cur2:
                            existing = fetch_account_by_uuid(cur2, opencloud_uuid)
                    if existing:
                        return False, "uuid_already_linked", {
                            "existing_email": existing["email"],
                            "opencloud_uuid": opencloud_uuid,
                        }
                return False, "conflict", None

            created = row[0]
            current_status = row[1]
            current_token = row[2]
            linked_uuid = row[3]
            # Email already linked to a different OpenCloud user
            if (
                opencloud_uuid
                and linked_uuid
                and linked_uuid != opencloud_uuid
                and not created
            ):
                conn.rollback()
                return False, "email_already_linked", {
                    "email": email,
                    "existing_opencloud_uuid": linked_uuid,
                }
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
        body = {"error": status}
        if extra:
            body.update(extra)
        code = 409 if status in ("uuid_already_linked", "email_already_linked", "conflict") else 400
        return jsonify(body), code

    code = 201 if status == "created" else 200
    body = {"ok": True, "email": (extra or {}).get("email", email), "status": status}
    if extra:
        body.update(extra)
    return jsonify(body), code


@app.route("/register", methods=["POST"])
def register():
    """Public, self-contained mailbox registration for the browser signup form.

    Reached via nginx `/api/register` -> :8092/register. No Bearer token (called
    from the browser); protected by per-IP rate limiting and freemail rejection.
    Public signups are never IDM-linked, so any `opencloud_uuid` in the body is
    ignored. Reuses `provision_mailbox` so it behaves exactly like `/provision`.
    """
    if not DB["password"]:
        return jsonify({"error": "service_unavailable"}), 503

    if rate_limited(client_ip()):
        return jsonify({"error": "rate_limited"}), 429

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or data.get("desired_email") or "").strip().lower()
    password = data.get("password")
    mail_mode = (data.get("mail_mode") or "km0").strip().lower()
    contact_email = (data.get("contact_email") or "").strip().lower() or None

    if mail_mode not in ("km0", "custom"):
        return jsonify({"error": "invalid_mail_mode"}), 400
    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "invalid_email"}), 400
    if not password or len(str(password)) < 8:
        return jsonify({"error": "password_too_short"}), 400
    lp_err = validate_local_part(email.split("@", 1)[0])
    if lp_err:
        return jsonify({"error": lp_err}), 400

    # opencloud_uuid intentionally forced to None: public signups are not IDM-linked.
    ok, status, extra = provision_mailbox(
        email, password, None, mail_mode, contact_email, send_verify=True
    )
    if not ok:
        body = {"error": status}
        if extra:
            body.update(extra)
        code = 409 if status in ("uuid_already_linked", "email_already_linked", "conflict") else 400
        return jsonify(body), code

    code = 201 if status == "created" else 200
    body = {"ok": True, "email": (extra or {}).get("email", email), "status": status}
    if extra:
        body.update(extra)
    if mail_mode == "custom":
        domain = domain_of(email)
        body["domain"] = domain
        body["continue_to"] = f"/domain.html?domain={domain}"
    return jsonify(body), code


@app.route("/activate", methods=["POST"])
def activate():
    """Activate Mail for an existing OpenCloud user (Google/OIDC Cloud IdP welcome).

    Provisions foo@km0digital.com, stores contact_email (often freemail), links opencloud_uuid.
    Primary UI lives in hub / register-api; this is the mail-side API those call.
    """
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    if not DB["password"]:
        return jsonify({"error": "service_unavailable"}), 503

    data = request.get_json(silent=True) or {}
    opencloud_uuid = (data.get("opencloud_uuid") or "").strip() or None
    contact_email = (data.get("contact_email") or "").strip().lower() or None
    password = data.get("password")
    mail_mode = (data.get("mail_mode") or "km0").strip().lower()
    send_verify = data.get("send_verification", True)
    local_part = (data.get("local_part") or data.get("username") or "").strip().lower()
    email = (data.get("email") or data.get("desired_email") or "").strip().lower()

    if not opencloud_uuid:
        return jsonify({"error": "missing_opencloud_uuid"}), 400
    if not contact_email or not EMAIL_RE.match(contact_email):
        return jsonify({"error": "missing_or_invalid_contact_email"}), 400
    if not password or len(str(password)) < 8:
        return jsonify({"error": "missing_or_weak_password"}), 400
    if mail_mode not in ("km0", "custom"):
        return jsonify({"error": "invalid_mail_mode"}), 400

    if not email:
        if not local_part:
            return jsonify({"error": "missing_local_part_or_email"}), 400
        lp_err = validate_local_part(local_part)
        if lp_err:
            return jsonify({"error": lp_err}), 400
        if mail_mode != "km0":
            return jsonify({"error": "local_part_requires_km0_mode"}), 400
        email = f"{local_part}@{MAIL_DOMAIN}"

    if is_freemail_domain(domain_of(email)):
        return jsonify(
            {
                "error": "freemail_blocked",
                "hint": "Mailbox must be @km0digital.com (or verified custom). Freemail is contact_email only.",
            }
        ), 400

    ok, status, extra = provision_mailbox(
        email, password, opencloud_uuid, mail_mode, contact_email, send_verify=send_verify
    )
    if not ok:
        body = {"error": status, "activate_required": status == "not_found"}
        if extra:
            body.update(extra)
        code = 409 if status in ("uuid_already_linked", "email_already_linked", "conflict") else 400
        return jsonify(body), code

    mailbox = (extra or {}).get("email", email)
    code = 201 if status == "created" else 200
    body = {
        "ok": True,
        "email": mailbox,
        "status": status,
        "opencloud_uuid": opencloud_uuid,
        "contact_email": contact_email,
        "entry": entry_hints(mailbox),
    }
    if extra:
        for key in ("verification_status", "mail_mode"):
            if key in extra:
                body[key] = extra[key]
    return jsonify(body), code


@app.route("/link", methods=["POST"])
def link():
    """Attach opencloud_uuid (+ optional contact_email) to an existing mailbox without re-provision."""
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    if not DB["password"]:
        return jsonify({"error": "service_unavailable"}), 503

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    opencloud_uuid = (data.get("opencloud_uuid") or "").strip() or None
    contact_email = (data.get("contact_email") or "").strip().lower() or None

    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "invalid_email"}), 400
    if not opencloud_uuid:
        return jsonify({"error": "missing_opencloud_uuid"}), 400
    if is_freemail_domain(domain_of(email)):
        return jsonify({"error": "freemail_blocked"}), 400

    with db_connect() as conn:
        with conn.cursor() as cur:
            existing_uuid = fetch_account_by_uuid(cur, opencloud_uuid)
            if existing_uuid and existing_uuid["email"] != email:
                return jsonify(
                    {
                        "error": "uuid_already_linked",
                        "existing_email": existing_uuid["email"],
                        "opencloud_uuid": opencloud_uuid,
                    }
                ), 409

            cur.execute(
                """
                SELECT email, opencloud_uuid, contact_email, verification_status, mail_mode, active
                FROM mail_accounts WHERE lower(email) = lower(%s)
                """,
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "not_found", "activate_required": True}), 404

            current = {
                "email": row[0],
                "opencloud_uuid": row[1],
                "contact_email": row[2],
                "verification_status": row[3],
                "mail_mode": row[4],
                "active": row[5],
            }
            if current["opencloud_uuid"] and current["opencloud_uuid"] != opencloud_uuid:
                return jsonify(
                    {
                        "error": "email_already_linked",
                        "email": email,
                        "existing_opencloud_uuid": current["opencloud_uuid"],
                    }
                ), 409

            cur.execute(
                """
                UPDATE mail_accounts
                SET opencloud_uuid = %s,
                    contact_email = COALESCE(%s, contact_email),
                    updated_at = NOW()
                WHERE lower(email) = lower(%s)
                RETURNING email, opencloud_uuid, contact_email, verification_status, mail_mode, active
                """,
                (opencloud_uuid, contact_email, email),
            )
            updated = cur.fetchone()
        conn.commit()

    payload = {
        "email": updated[0],
        "opencloud_uuid": updated[1],
        "contact_email": updated[2],
        "verification_status": updated[3],
        "mail_mode": updated[4],
        "active": updated[5],
    }
    return jsonify(
        {
            "ok": True,
            "status": "linked",
            **account_payload(payload),
            "entry": entry_hints(payload["email"]),
        }
    )


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


@app.route("/lookup/by-uuid/<path:opencloud_uuid>", methods=["GET"])
def lookup_by_uuid(opencloud_uuid: str):
    """Hub / activate-mail: resolve mailbox for an OpenCloud user id."""
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    opencloud_uuid = (opencloud_uuid or "").strip()
    if not opencloud_uuid:
        return jsonify({"error": "missing_uuid"}), 400
    with db_connect() as conn:
        with conn.cursor() as cur:
            row = fetch_account_by_uuid(cur, opencloud_uuid)
    if not row:
        return jsonify(
            {
                "error": "not_found",
                "activate_required": True,
                "hint": "No mailbox linked; call POST /activate with local_part + contact_email.",
            }
        ), 404
    return jsonify({"ok": True, "activate_required": False, **account_payload(row)})


@app.route("/lookup/by-contact/<path:contact_email>", methods=["GET"])
def lookup_by_contact(contact_email: str):
    """Hub / SSO: resolve mailbox(es) by freemail contact_email."""
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    contact_email = (contact_email or "").strip().lower()
    if not contact_email or not EMAIL_RE.match(contact_email):
        return jsonify({"error": "invalid_email"}), 400
    with db_connect() as conn:
        with conn.cursor() as cur:
            rows = fetch_account_by_contact(cur, contact_email)
    if not rows:
        return jsonify(
            {
                "error": "not_found",
                "activate_required": True,
                "hint": "No mailbox for this contact_email; offer Activate Mail.",
            }
        ), 404
    return jsonify(
        {
            "ok": True,
            "activate_required": False,
            "accounts": [account_payload(r) for r in rows],
        }
    )


@app.route("/account/<path:email>/status", methods=["GET"])
def account_status(email: str):
    email = email.strip().lower()
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT verification_status, mail_mode, active, opencloud_uuid, contact_email
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
            "opencloud_uuid": row[3],
            "contact_email": row[4],
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


# --------------------------------------------------------------------------
# Self-service custom domains (Phase 2). Owner-scoped, Bearer-protected: only
# the Roundcube km0_domains plugin calls these server-to-server, passing the
# authenticated session user as `owner`. Never expose without the token — the
# owner param is trusted precisely because the caller holds the shared Bearer.
# --------------------------------------------------------------------------


def _require_owner(source) -> tuple[str | None, tuple]:
    owner = (source.get("owner") or "").strip().lower()
    if not owner or not EMAIL_RE.match(owner):
        return None, (jsonify({"error": "invalid_owner"}), 400)
    return owner, ()


@app.route("/my/domains", methods=["GET"])
def my_domains_list():
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    owner, err = _require_owner(request.args)
    if err:
        return err
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name, verification_status, active
                FROM mail_domains
                WHERE lower(owner_email) = %s
                ORDER BY name
                """,
                (owner,),
            )
            rows = cur.fetchall()
    return jsonify(
        {
            "domains": [
                {"name": r[0], "verification_status": r[1], "active": r[2]}
                for r in rows
            ]
        }
    )


@app.route("/my/domains", methods=["POST"])
def my_domains_add():
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    if not DB["password"]:
        return jsonify({"error": "service_unavailable"}), 503
    data = request.get_json(silent=True) or {}
    owner, err = _require_owner(data)
    if err:
        return err
    domain = normalize_domain(data.get("domain"))
    if not domain:
        return jsonify({"error": "invalid_domain"}), 400
    if domain == MAIL_DOMAIN or is_freemail_domain(domain):
        return jsonify({"error": "invalid_domain"}), 400

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_email FROM mail_domains WHERE lower(name) = %s",
                (domain,),
            )
            row = cur.fetchone()
            if row and row[0] and row[0].lower() != owner:
                return jsonify({"error": "domain_taken"}), 409
            cur.execute(
                """
                INSERT INTO mail_domains (
                    name, active, owner_email, verification_token,
                    verification_status, mx_verified, spf_verified, dkim_verified, txt_verified
                ) VALUES (%s, FALSE, %s, %s, 'pending', FALSE, FALSE, FALSE, FALSE)
                ON CONFLICT (name) DO UPDATE SET
                    owner_email = COALESCE(mail_domains.owner_email, EXCLUDED.owner_email),
                    verification_token = COALESCE(mail_domains.verification_token, EXCLUDED.verification_token)
                """,
                (domain, owner, secrets.token_urlsafe(24)),
            )
        conn.commit()
    return jsonify({"ok": True, "domain": domain}), 201


@app.route("/my/domains/<path:domain>", methods=["DELETE"])
def my_domains_delete(domain: str):
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    owner, err = _require_owner(request.args)
    if err:
        return err
    domain = (domain or "").strip().lower()
    if domain == MAIL_DOMAIN:
        return jsonify({"error": "forbidden"}), 403
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_email FROM mail_domains WHERE lower(name) = %s",
                (domain,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            if not row[0] or row[0].lower() != owner:
                return jsonify({"error": "forbidden"}), 403
            cur.execute(
                "DELETE FROM mail_aliases WHERE split_part(alias_address, '@', 2) = %s",
                (domain,),
            )
            cur.execute(
                "DELETE FROM mail_accounts WHERE split_part(email, '@', 2) = %s",
                (domain,),
            )
            cur.execute("DELETE FROM mail_domains WHERE lower(name) = %s", (domain,))
        conn.commit()
    reload_postfix_maps()
    return jsonify({"ok": True, "domain": domain})


@app.route("/my/addresses", methods=["GET"])
def my_addresses_list():
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    owner, err = _require_owner(request.args)
    if err:
        return err
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.email, a.verification_status, a.active, split_part(a.email, '@', 2) AS domain
                FROM mail_accounts a
                JOIN mail_domains d ON lower(d.name) = split_part(a.email, '@', 2)
                WHERE lower(d.owner_email) = %s
                ORDER BY a.email
                """,
                (owner,),
            )
            rows = cur.fetchall()
    return jsonify(
        {
            "addresses": [
                {
                    "email": r[0],
                    "verification_status": r[1],
                    "active": r[2],
                    "domain": r[3],
                }
                for r in rows
            ]
        }
    )


@app.route("/my/addresses", methods=["POST"])
def my_addresses_add():
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    if not DB["password"]:
        return jsonify({"error": "service_unavailable"}), 503
    data = request.get_json(silent=True) or {}
    owner, err = _require_owner(data)
    if err:
        return err
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    if not email or not EMAIL_RE.match(email):
        return jsonify({"error": "invalid_email"}), 400
    if not password or len(str(password)) < 8:
        return jsonify({"error": "password_too_short"}), 400
    lp_err = validate_local_part(email.split("@", 1)[0])
    if lp_err:
        return jsonify({"error": lp_err}), 400

    domain = domain_of(email)
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_email, active FROM mail_domains WHERE lower(name) = %s",
                (domain,),
            )
            row = cur.fetchone()
    if not row or not row[0] or row[0].lower() != owner:
        return jsonify({"error": "forbidden"}), 403
    if not row[1]:
        return jsonify({"error": "domain_not_active"}), 409

    ok, status, extra = provision_mailbox(
        email, password, None, "custom", None, send_verify=False
    )
    if not ok:
        body = {"error": status}
        if extra:
            body.update(extra)
        code = 409 if status in ("conflict", "email_already_linked") else 400
        return jsonify(body), code

    # Domain is verified, so the new mailbox can send immediately.
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE mail_accounts
                SET verification_status = 'verified', verification_token = NULL, updated_at = NOW()
                WHERE lower(email) = %s
                """,
                (email,),
            )
        conn.commit()

    code = 201 if status == "created" else 200
    return jsonify({"ok": True, "email": email, "status": status, "verification_status": "verified"}), code


@app.route("/my/addresses/<path:email>", methods=["DELETE"])
def my_addresses_delete(email: str):
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    owner, err = _require_owner(request.args)
    if err:
        return err
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        return jsonify({"error": "invalid_email"}), 400
    domain = domain_of(email)
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT owner_email FROM mail_domains WHERE lower(name) = %s",
                (domain,),
            )
            row = cur.fetchone()
            if not row or not row[0] or row[0].lower() != owner:
                return jsonify({"error": "forbidden"}), 403
            cur.execute("DELETE FROM mail_aliases WHERE lower(alias_address) = %s", (email,))
            cur.execute("DELETE FROM mail_accounts WHERE lower(email) = %s", (email,))
            deleted = cur.rowcount
        conn.commit()
    if not deleted:
        return jsonify({"error": "not_found"}), 404
    reload_postfix_maps()
    return jsonify({"ok": True, "email": email})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=LISTEN_PORT)
