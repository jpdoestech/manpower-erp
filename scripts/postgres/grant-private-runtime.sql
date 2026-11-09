BEGIN;

-- Pin the reviewed privilege list to the migration it was tested against.
DO $$
BEGIN
    IF current_user <> 'erp_migrator' OR current_schema() <> 'erp_private' THEN
        RAISE EXCEPTION 'Run as erp_migrator with the private search path';
    END IF;
    IF (SELECT array_agg(version_num) FROM erp_private.alembic_version)
        IS DISTINCT FROM ARRAY['0004_sqlite_constraints']::varchar[] THEN
        RAISE EXCEPTION 'Unexpected Alembic revision. Review runtime privileges before proceeding';
    END IF;
END
$$;

GRANT SELECT, INSERT, UPDATE ON erp_private.auth_users, erp_private.auth_sessions,
    erp_private.auth_login_limits, erp_private.auth_account_changes,
    erp_private.auth_password_resets TO erp_runtime;
GRANT DELETE ON erp_private.auth_login_limits TO erp_runtime;
GRANT INSERT, SELECT (created_at) ON erp_private.auth_events TO erp_runtime;

COMMIT;
