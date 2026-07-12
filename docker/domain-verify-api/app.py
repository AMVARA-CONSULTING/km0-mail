#!/usr/bin/env python3
"""DNS verification API for custom domains (Model B)."""

import base64
import logging
import os
import re
import secrets
import subprocess

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

DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$", re.I)

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

    token, vstatus, active, txt_v, mx_v, spf_v, dkim_v, selector, dkim_dns = row
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
    if not auth_ok():
        return jsonify({"error": "unauthorized"}), 401

    domain = domain.strip().lower()
    if not DOMAIN_RE.match(domain) or domain == MAIL_DOMAIN:
        return jsonify({"error": "invalid_domain"}), 400

    with db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT verification_token, dkim_selector, dkim_public_key
                FROM mail_domains WHERE name = %s
                """,
                (domain,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "not_found"}), 404

            token, selector, dkim_dns = row
            if not dkim_dns:
                _, dkim_dns = generate_dkim_keypair()
                cur.execute(
                    "UPDATE mail_domains SET dkim_public_key = %s, dkim_selector = COALESCE(dkim_selector, 'mail') WHERE name = %s",
                    (dkim_dns, domain),
                )
                selector = selector or "mail"

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
        reload_postfix_maps()

    return jsonify({"domain": domain, "active": active, "verification_status": vstatus, "checks": checks})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=LISTEN_PORT)
