-- Phase 2: self-service custom domains — ownership by mailbox email.
-- Password-only users have opencloud_uuid NULL, so owner_opencloud_uuid cannot
-- scope domains for them. Track the mailbox (email) that manages each domain.

ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS owner_email VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_mail_domains_owner_email ON mail_domains (lower(owner_email));

-- Backfill best-effort: adopt the earliest custom mailbox on each domain as its
-- owner. Leaves owner_email NULL when no custom mailbox matches. Never touches
-- the shared km0digital.com domain (it has no single owner).
UPDATE mail_domains d
SET owner_email = sub.email
FROM (
    SELECT DISTINCT ON (split_part(email, '@', 2))
        split_part(email, '@', 2) AS dom,
        email
    FROM mail_accounts
    WHERE mail_mode = 'custom'
    ORDER BY split_part(email, '@', 2), id
) sub
WHERE d.owner_email IS NULL
  AND lower(d.name) = lower(sub.dom)
  AND d.name <> 'km0digital.com';
