DO $$
BEGIN
    -- Ownership confers DDL authority independently of schema CREATE grants.
    IF EXISTS (SELECT 1 FROM pg_namespace
               WHERE nspname = 'erp_private' AND nspowner <> 'erp_migrator'::regrole)
        OR EXISTS (SELECT 1 FROM pg_class
                   WHERE relnamespace = 'erp_private'::regnamespace
                     AND relowner <> 'erp_migrator'::regrole)
        OR EXISTS (SELECT 1 FROM pg_proc
                   WHERE pronamespace = 'erp_private'::regnamespace
                     AND proowner <> 'erp_migrator'::regrole) THEN
        RAISE EXCEPTION 'ERP schema, relations and routines must be owned by erp_migrator';
    END IF;

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

    IF (SELECT count(*) FROM pg_class WHERE relnamespace = 'erp_private'::regnamespace
        AND relname IN ('org_companies', 'org_company_grants', 'org_company_events',
                        'org_head_offices', 'org_branches', 'org_hierarchy_events')
        AND relrowsecurity) <> 6
        OR has_table_privilege('erp_runtime', 'erp_private.org_company_grants',
                              'INSERT, UPDATE, DELETE, TRUNCATE')
        OR has_table_privilege('erp_runtime', 'erp_private.org_companies', 'INSERT, DELETE, TRUNCATE')
        OR has_table_privilege('erp_runtime', 'erp_private.org_company_events', 'UPDATE, DELETE, TRUNCATE') THEN
        RAISE EXCEPTION 'Unexpected company isolation or provisioning privileges';
    END IF;

    IF has_table_privilege('erp_runtime', 'erp_private.org_head_offices', 'DELETE, TRUNCATE')
        OR has_table_privilege('erp_runtime', 'erp_private.org_branches', 'DELETE, TRUNCATE')
        OR has_table_privilege('erp_runtime', 'erp_private.org_hierarchy_events', 'UPDATE, DELETE, TRUNCATE')
        OR EXISTS (
            SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
            WHERE c.relnamespace='erp_private'::regnamespace
              AND c.relname IN ('org_head_offices', 'org_branches')
              AND a.attname IN ('id', 'company_id', 'head_office_id', 'code',
                               'valid_from', 'created_by', 'created_at')
              AND has_column_privilege('erp_runtime', c.oid, a.attnum, 'UPDATE')
        ) THEN
        RAISE EXCEPTION 'Unexpected hierarchy mutation or parent privileges';
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
