#!/usr/bin/env python3
"""DNS verification API for custom domains (Model B)."""

import base64
import logging
import os
import re
import secrets
import subprocess
import threading
import time

import psycopg2
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("domain-verify-api")

MAIL_HOSTNAME = os.environ.get("MAIL_HOSTNAME", "mail.km0digital.com")
MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN", "km0digital.com")
API_TOKEN = os.environ.get("DOMAIN_VERIFY_API_TOKEN", os.environ.get("MAIL_PROVISION_API_TOKEN", ""))
LISTEN_PORT = int(os.environ.get("PORT", "8093"))
COMPOSE_PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", "km0-mail")
DKIM_CONF_PATH = os.environ.get("DKIM_CONF_PATH", "/config/rspamd/local.d/dkim_signing.conf")
RSPAMD_CONTAINER = os.environ.get("RSPAMD_CONTAINER", f"{COMPOSE_PROJECT}-rspamd-1")
# Generic per-domain key map in dkim_signing.conf: "$domain.$selector.key".
DKIM_KEY_DIR = os.environ.get("DKIM_KEY_DIR", "/var/lib/rspamd/dkim")

# Public /check throttle (per client IP; in-process, dependency-light) — the DNS
# wizard calls /check unauthenticated, so guard against abuse of DNS/key work.
CHECK_RATE_MAX = int(os.environ.get("CHECK_RATE_MAX", "20"))
CHECK_RATE_WINDOW = int(os.environ.get("CHECK_RATE_WINDOW_SEC", "300"))

DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$", re.I)
SELECTOR_RE = re.compile(r"^[a-z0-9._-]+$", re.I)

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
    import secrets as sec

    return sec.compare_digest(auth[7:], API_TOKEN)


def dig_txt(name: str) -> list[str]:
    try:
        out = subprocess.check_output(["dig", "+short", "TXT", name], timeout=10, text=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        log.warning("dig TXT %s failed: %s", name, exc)
        return []
    records = []
    for line in out.strip().splitlines():
        line = line.strip().strip('"')
        if line:
            records.append(line)
    return records


def dig_mx(domain: str) -> list[tuple[int, str]]:
    try:
        out = subprocess.check_output(["dig", "+short", "MX", domain], timeout=10, text=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    results = []
    for line in out.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            prio = int(parts[0])
            host = parts[1].rstrip(".").lower()
            results.append((prio, host))
    return results


def generate_dkim_keypair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    pub_b64 = base64.b64encode(pub).decode()
    dns_value = f"v=DKIM1; k=rsa; p={pub_b64}"
    return private_pem, dns_value


def reload_postfix_maps() -> None:
    container = os.environ.get("POSTFIX_CONTAINER", f"{COMPOSE_PROJECT}-postfix-1")
    try:
        subprocess.run(["docker", "exec", container, "build-hash-maps.sh"], check=True, timeout=60, capture_output=True)
    except Exception as exc:
        log.warning("postfix reload skipped: %s", exc)


def reload_rspamd() -> None:
    """Soft-reload Rspamd (SIGHUP to PID 1) so a freshly materialized DKIM key is
    picked up and any negative key-cache entry is cleared. Best-effort."""
    try:
        subprocess.run(
            ["docker", "kill", "--signal=HUP", RSPAMD_CONTAINER],
            check=True, timeout=30, capture_output=True,
        )
    except Exception as exc:
        log.warning("rspamd reload skipped: %s", exc)


def materialize_dkim_key(domain: str, selector: str, private_pem: str) -> bool:
    """Write the domain's DKIM private key into Rspamd's key store at the path the
    generic `$domain.$selector.key` map expects, then reload Rspamd.

    Runs as the container's default user (`_rspamd`) via `docker exec`, so the file
    is owned by Rspamd and created with umask 077 (0600). Idempotent; also recovers
    the key on Rspamd volume loss (re-materializes from the DB on the next check)."""
    if not private_pem:
        return False
    sel = selector if selector and SELECTOR_RE.match(selector) else "mail"
    key_path = f"{DKIM_KEY_DIR}/{domain}.{sel}.key"
    try:
        subprocess.run(
            [
                "docker", "exec", "-i", RSPAMD_CONTAINER, "sh", "-c",
                f"umask 077; mkdir -p {DKIM_KEY_DIR} && cat > {key_path}",
            ],
            input=private_pem.encode(),
            check=True, timeout=30, capture_output=True,
        )
    except Exception as exc:
        log.warning("rspamd dkim key materialize failed for %s: %s", domain, exc)
        return False
    reload_rspamd()
    log.info("materialized DKIM key for %s at %s", domain, key_path)
    return True


_rate_lock = threading.Lock()
_rate_hits: dict[str, list[float]] = {}


def client_ip() -> str:
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or request.remote_addr or "unknown"


def rate_limited(ip: str) -> bool:
    now = time.time()
    with _rate_lock:
        hits = [t for t in _rate_hits.get(ip, []) if now - t < CHECK_RATE_WINDOW]
        if len(hits) >= CHECK_RATE_MAX:
            _rate_hits[ip] = hits
            return True
        hits.append(now)
        _rate_hits[ip] = hits
        if len(_rate_hits) > 10000:
            for key in [k for k, v in _rate_hits.items() if all(now - t >= CHECK_RATE_WINDOW for t in v)]:
                del _rate_hits[key]
    return False


def ensure_domain_keys(cur, domain: str, selector: str | None) -> tuple[str, str | None, str | None]:
    """Ensure the domain has a DKIM keypair persisted; generate + store BOTH the
    public (DNS value) and private (PEM) keys when missing. Returns
    (selector, dkim_dns_value, private_pem)."""
    cur.execute(
        "SELECT dkim_selector, dkim_public_key, dkim_private_key FROM mail_domains WHERE name = %s",
        (domain,),
    )
    row = cur.fetchone()
    if not row:
        return (selector or "mail"), None, None
    sel = row[0] or selector or "mail"
    dkim_dns, private_pem = row[1], row[2]
    if not dkim_dns or not private_pem:
        private_pem, dkim_dns = generate_dkim_keypair()
        cur.execute(
            """
            UPDATE mail_domains SET
                dkim_public_key = %s,
                dkim_private_key = %s,
                dkim_selector = COALESCE(dkim_selector, 'mail')
            WHERE name = %s
            """,
            (dkim_dns, private_pem, domain),
        )
    return sel, dkim_dns, private_pem


def check_domain(domain: str, token: str, selector: str, dkim_dns: str | None) -> dict:
    txt_ok = any(f"km0-mail-verification={token}" in r.replace(" ", "") for r in dig_txt(domain))
    mx_ok = any(host == MAIL_HOSTNAME.lower() for _, host in dig_mx(domain))
    spf_records = dig_txt(domain)
    spf_ok = any("v=spf1" in r and MAIL_HOSTNAME.lower() in r.lower() for r in spf_records)
    dkim_name = f"{selector}._domainkey.{domain}"
    dkim_records = dig_txt(dkim_name)
    dkim_ok = False
    if dkim_dns:
        dkim_ok = any(dkim_dns.split("p=")[1][:32] in r.replace(" ", "") for r in dkim_records if "p=" in dkim_dns)
    return {
        "txt_verified": txt_ok,
        "mx_verified": mx_ok,
        "spf_verified": spf_ok,
        "dkim_verified": dkim_ok,
        "all_verified": txt_ok and mx_ok and spf_ok and dkim_ok,
    }


def dns_instructions(domain: str, token: str, selector: str, dkim_dns: str | None) -> dict:
    return {
        "txt": {"host": "@", "value": f"km0-mail-verification={token}"},
        "mx": {"host": "@", "value": MAIL_HOSTNAME, "priority": 10},
        "spf": {"host": "@", "value": f"v=spf1 mx a:{MAIL_HOSTNAME} ~all"},
        "dkim": {"host": f"{selector}._domainkey", "value": dkim_dns or "(generating...)"},
    }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": bool(DB["password"]), "hostname": MAIL_HOSTNAME})


@app.route("/domain/<domain>/status", methods=["GET"])
def domain_status(domain: str):
    domain = domain.strip().lower()
    if not DOMAIN_RE.match(domain) or domain == MAIL_DOMAIN:
        return jsonify({"error": "invalid_domain"}), 400

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT verification_token, verification_status, active,
                       txt_verified, mx_verified, spf_verified, dkim_verified,
                       dkim_selector, dkim_public_key
                FROM mail_domains WHERE name = %s
                """,
                (domain,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            # First view of the wizard generates+persists the keypair so the DKIM
            # record can be shown for the operator to publish at their registrar.
            selector, dkim_dns, _ = ensure_domain_keys(cur, domain, row[7])
        conn.commit()

    token, vstatus, active, txt_v, mx_v, spf_v, dkim_v = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
    instructions = dns_instructions(domain, token, selector or "mail", dkim_dns)
    return jsonify(
        {
            "domain": domain,
            "verification_status": vstatus,
            "active": active,
            "checks": {
                "txt_verified": txt_v,
                "mx_verified": mx_v,
                "spf_verified": spf_v,
                "dkim_verified": dkim_v,
            },
            "dns": instructions,
        }
    )


@app.route("/domain/<domain>/check", methods=["POST"])
def domain_check(domain: str):
    # The public DNS wizard (domain.html) calls this unauthenticated, so auth is
    # optional but a supplied Bearer token must still be valid (operator path).
    # Activation only ever succeeds when the caller genuinely controls the domain's
    # DNS (MX/TXT/SPF/DKIM must resolve to us), so a per-IP throttle is enough.
    if request.headers.get("Authorization") and not auth_ok():
        return jsonify({"error": "unauthorized"}), 401
    if rate_limited(client_ip()):
        return jsonify({"error": "rate_limited"}), 429

    domain = domain.strip().lower()
    if not DOMAIN_RE.match(domain) or domain == MAIL_DOMAIN:
        return jsonify({"error": "invalid_domain"}), 400

    private_pem = None
    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT verification_token FROM mail_domains WHERE name = %s",
                (domain,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404
            token = row[0]

            selector, dkim_dns, private_pem = ensure_domain_keys(cur, domain, None)

            checks = check_domain(domain, token, selector or "mail", dkim_dns)

            cur.execute(
                """
                UPDATE mail_domains SET
                    txt_verified = %s, mx_verified = %s, spf_verified = %s, dkim_verified = %s,
                    active = %s,
                    verification_status = CASE WHEN %s THEN 'verified' ELSE 'pending' END
                WHERE name = %s
                RETURNING active, verification_status
                """,
                (
                    checks["txt_verified"],
                    checks["mx_verified"],
                    checks["spf_verified"],
                    checks["dkim_verified"],
                    checks["all_verified"],
                    checks["all_verified"],
                    domain,
                ),
            )
            active, vstatus = cur.fetchone()

            if checks["all_verified"]:
                cur.execute(
                    """
                    UPDATE mail_accounts SET verification_status = 'verified', updated_at = NOW()
                    WHERE mail_mode = 'custom' AND lower(split_part(email, '@', 2)) = %s
                    """,
                    (domain,),
                )
        conn.commit()

    if checks["all_verified"]:
        # Inbound: Postfix accepts the now-active domain from the DB.
        reload_postfix_maps()
        # Outbound: materialize the domain's own DKIM key so Rspamd signs with it.
        materialize_dkim_key(domain, selector or "mail", private_pem)

    return jsonify({"domain": domain, "active": active, "verification_status": vstatus, "checks": checks})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=LISTEN_PORT)
