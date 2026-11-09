BEGIN;

DO $$
BEGIN
    IF (SELECT count(*) FROM pg_roles
        WHERE rolname IN ('erp_migrator', 'erp_runtime') AND rolcanlogin
          AND NOT (rolsuper OR rolcreaterole OR rolcreatedb OR rolreplication OR rolbypassrls)) <> 2
        OR EXISTS (
            SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member
            WHERE r.rolname IN ('erp_migrator', 'erp_runtime')
        )
        OR has_schema_privilege('erp_migrator', 'public', 'CREATE')
        OR has_schema_privilege('erp_runtime', 'public', 'CREATE') THEN
        RAISE EXCEPTION 'Expected separate unprivileged login roles without membership or public CREATE';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname <> 'erp_private'
          AND c.relname IN ('alembic_version', 'auth_users', 'auth_sessions', 'auth_login_limits',
                           'auth_events', 'auth_account_changes', 'auth_password_resets')
    ) THEN
        RAISE EXCEPTION 'ERP objects already exist outside the private schema';
    END IF;

    EXECUTE format('ALTER ROLE erp_migrator IN DATABASE %I SET search_path = erp_private, pg_temp',
                   current_database());
    EXECUTE format('ALTER ROLE erp_runtime IN DATABASE %I SET search_path = erp_private, pg_temp',
                   current_database());
END
$$;

CREATE SCHEMA IF NOT EXISTS erp_private AUTHORIZATION erp_migrator;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_namespace
                   WHERE nspname = 'erp_private' AND nspowner = 'erp_migrator'::regrole) THEN
        RAISE EXCEPTION 'Unexpected owner of erp_private';
    END IF;
END
$$;

REVOKE ALL ON SCHEMA erp_private FROM PUBLIC, anon, authenticated, service_role, erp_runtime;
GRANT USAGE ON SCHEMA erp_private TO erp_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE erp_migrator REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

COMMIT;
