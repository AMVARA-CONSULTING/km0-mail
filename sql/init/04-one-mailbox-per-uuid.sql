-- Issue #13: enforce 1 mailbox per opencloud_uuid + contact_email lookup index.
-- Safe to re-run (IF NOT EXISTS). Also applied via 03-registration-schema.sql on fresh installs.

WITH dups AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY opencloud_uuid ORDER BY id) AS rn
    FROM mail_accounts
    WHERE opencloud_uuid IS NOT NULL
)
UPDATE mail_accounts a
SET opencloud_uuid = NULL,
    updated_at = NOW()
FROM dups d
WHERE a.id = d.id
  AND d.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mail_accounts_opencloud_uuid_unique
    ON mail_accounts (opencloud_uuid)
    WHERE opencloud_uuid IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_mail_accounts_contact_email
    ON mail_accounts (lower(contact_email))
    WHERE contact_email IS NOT NULL;
