#!/bin/bash
set -euo pipefail

# Bootstrap PostgreSQL roles and Roundcube database from compose env vars.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${MAIL_DB_USER}') THEN
            CREATE ROLE ${MAIL_DB_USER} LOGIN PASSWORD '${MAIL_DB_PASSWORD}';
        ELSE
            ALTER ROLE ${MAIL_DB_USER} WITH PASSWORD '${MAIL_DB_PASSWORD}';
        END IF;
    END
    \$\$;
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${MAIL_DB_USER};
    GRANT USAGE ON SCHEMA public TO ${MAIL_DB_USER};
    GRANT SELECT ON mail_domains, mail_accounts, mail_aliases TO ${MAIL_DB_USER};
    GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA public TO ${MAIL_DB_USER};
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${ROUNDCUBE_DB_USER}') THEN
            CREATE ROLE ${ROUNDCUBE_DB_USER} LOGIN PASSWORD '${ROUNDCUBE_DB_PASSWORD}';
        ELSE
            ALTER ROLE ${ROUNDCUBE_DB_USER} WITH PASSWORD '${ROUNDCUBE_DB_PASSWORD}';
        END IF;
    END
    \$\$;
EOSQL

if ! psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${ROUNDCUBE_DB_NAME}'" | grep -q 1; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
        -c "CREATE DATABASE ${ROUNDCUBE_DB_NAME} OWNER ${ROUNDCUBE_DB_USER};"
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$ROUNDCUBE_DB_NAME" <<-EOSQL
    GRANT ALL ON SCHEMA public TO ${ROUNDCUBE_DB_USER};
EOSQL
