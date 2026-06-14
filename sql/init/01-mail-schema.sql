-- km0-mail PostgreSQL schema (phase 1)
-- Virtual users, aliases, and Roundcube database bootstrap.

CREATE TABLE mail_domains (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE mail_accounts (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    opencloud_uuid  VARCHAR(64) NULL,
    quota_bytes     BIGINT NULL,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE mail_aliases (
    id              SERIAL PRIMARY KEY,
    alias_address   VARCHAR(255) NOT NULL UNIQUE,
    target_email    VARCHAR(255) NOT NULL REFERENCES mail_accounts(email) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO mail_domains (name) VALUES ('km0digital.com');

CREATE INDEX idx_mail_accounts_active ON mail_accounts (active) WHERE active = TRUE;
CREATE INDEX idx_mail_aliases_target ON mail_aliases (target_email);
