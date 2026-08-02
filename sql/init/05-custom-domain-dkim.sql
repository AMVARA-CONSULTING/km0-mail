-- Custom-domain DKIM private key persistence (Model B).
-- Store the DKIM private PEM in the trusted DB so Rspamd can (re)materialize the
-- signing key for a verified custom domain even after a volume loss.
-- Safe to re-run (IF NOT EXISTS guard).

ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS dkim_private_key TEXT;
