DO $$
BEGIN
    IF NOT has_schema_privilege('erp_runtime', 'erp_private', 'USAGE')
        OR has_schema_privilege('erp_runtime', 'erp_private', 'CREATE')
        OR has_schema_privilege('erp_runtime', 'public', 'CREATE')
        OR has_database_privilege('erp_runtime', current_database(), 'CREATE')
        OR has_table_privilege('erp_runtime', 'erp_private.alembic_version',
                               'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')
        OR has_table_privilege('erp_runtime', 'erp_private.auth_events', 'UPDATE, DELETE, TRUNCATE')
        OR NOT has_table_privilege('erp_runtime', 'erp_private.auth_events', 'INSERT') THEN
        RAISE EXCEPTION 'Unexpected ERP runtime privileges';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_roles r CROSS JOIN pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE r.rolname IN ('anon', 'authenticated', 'service_role')
          AND n.nspname = 'erp_private' AND c.relkind = 'r'
          AND (has_schema_privilege(r.oid, n.oid, 'USAGE, CREATE')
               OR has_table_privilege(r.oid, c.oid, 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')
               OR has_any_column_privilege(r.oid, c.oid, 'SELECT, INSERT, UPDATE, REFERENCES'))
    ) THEN
        RAISE EXCEPTION 'Supabase API roles must have no access to ERP schema or tables';
    END IF;
END
$$;
