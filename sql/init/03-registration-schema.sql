-- Registration schema extensions (Model A + Model B)
-- Safe to re-run on existing databases (IF NOT EXISTS guards).

ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS owner_opencloud_uuid VARCHAR(64);
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64);
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20) DEFAULT 'verified';
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS mx_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS spf_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS dkim_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS txt_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS dkim_selector VARCHAR(32) DEFAULT 'mail';
ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS dkim_public_key TEXT;

ALTER TABLE mail_accounts ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE mail_accounts ADD COLUMN IF NOT EXISTS verification_token VARCHAR(64);
ALTER TABLE mail_accounts ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
ALTER TABLE mail_accounts ADD COLUMN IF NOT EXISTS mail_mode VARCHAR(10);

-- Existing operational mailboxes: treat as verified (preserve user data)
UPDATE mail_accounts
SET verification_status = 'verified',
    mail_mode = COALESCE(mail_mode, 'km0')
WHERE verification_status IS NULL;

UPDATE mail_accounts
SET verification_status = 'verified',
    mail_mode = 'km0'
WHERE email IN ('postmaster@km0digital.com', 'noreply@km0digital.com');

UPDATE mail_domains
SET verification_status = 'verified',
    mx_verified = TRUE,
    spf_verified = TRUE,
    dkim_verified = TRUE,
    txt_verified = TRUE
WHERE name = 'km0digital.com';

CREATE INDEX IF NOT EXISTS idx_mail_accounts_verification ON mail_accounts (verification_status);
CREATE INDEX IF NOT EXISTS idx_mail_domains_owner ON mail_domains (owner_opencloud_uuid);

-- One mailbox per OpenCloud user (issue #13). Deduplicate legacy rows before unique index.
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
