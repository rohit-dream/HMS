"""Canonical SQL for platform.create_tenant() — single source for Alembic migrations."""

from __future__ import annotations

CREATE_TENANT_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION platform.create_tenant(
    p_name      VARCHAR,
    p_slug      VARCHAR,
    p_email     VARCHAR,
    p_subdomain VARCHAR DEFAULT NULL,
    p_country   VARCHAR DEFAULT 'IN',
    p_timezone  VARCHAR DEFAULT 'Asia/Kolkata',
    p_currency  VARCHAR DEFAULT 'INR'
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = platform, public
AS $$
DECLARE
    v_id              UUID;
    v_slug            VARCHAR(100);
    v_subdomain       VARCHAR(100);
    v_email           VARCHAR(255);
    v_reserved_slugs  TEXT[] := ARRAY[
        'admin', 'api', 'app', 'assets', 'auth', 'billing', 'dashboard',
        'docs', 'health', 'help', 'login', 'platform', 'register', 'static',
        'support', 'system', 'www'
    ];
BEGIN
    v_slug := lower(trim(p_slug));
    v_subdomain := lower(trim(COALESCE(p_subdomain, p_slug)));
    v_email := lower(trim(p_email));

    IF p_name IS NULL OR trim(p_name) = '' THEN
        RAISE EXCEPTION 'tenant name is required' USING ERRCODE = '22023';
    END IF;

    IF v_slug IS NULL OR v_slug = '' THEN
        RAISE EXCEPTION 'tenant slug is required' USING ERRCODE = '22023';
    END IF;

    IF v_slug !~ '^[a-z0-9]+(?:-[a-z0-9]+)*$' THEN
        RAISE EXCEPTION 'invalid tenant slug format' USING ERRCODE = '22023';
    END IF;

    IF length(v_slug) < 3 OR length(v_slug) > 100 THEN
        RAISE EXCEPTION 'tenant slug must be between 3 and 100 characters' USING ERRCODE = '22023';
    END IF;

    IF v_slug = ANY (v_reserved_slugs) OR v_subdomain = ANY (v_reserved_slugs) THEN
        RAISE EXCEPTION 'tenant slug is reserved' USING ERRCODE = '22023';
    END IF;

    IF v_email IS NULL OR v_email = '' OR v_email !~ '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$' THEN
        RAISE EXCEPTION 'invalid tenant email' USING ERRCODE = '22023';
    END IF;

    IF EXISTS (
        SELECT 1 FROM platform.tenants
        WHERE deleted_at IS NULL AND slug = v_slug
    ) THEN
        RAISE EXCEPTION 'tenant slug already exists' USING ERRCODE = '23505';
    END IF;

    IF EXISTS (
        SELECT 1 FROM platform.tenants
        WHERE deleted_at IS NULL AND subdomain = v_subdomain
    ) THEN
        RAISE EXCEPTION 'tenant subdomain already exists' USING ERRCODE = '23505';
    END IF;

    v_id := gen_random_uuid();

    INSERT INTO platform.tenants (
        id, tenant_id, name, slug, subdomain, status, email,
        country, timezone, currency
    ) VALUES (
        v_id, v_id, trim(p_name), v_slug, v_subdomain, 'trial', v_email,
        COALESCE(NULLIF(trim(p_country), ''), 'IN'),
        COALESCE(NULLIF(trim(p_timezone), ''), 'Asia/Kolkata'),
        COALESCE(NULLIF(trim(p_currency), ''), 'INR')
    );

    RETURN v_id;
END;
$$;

COMMENT ON FUNCTION platform.create_tenant(
    VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR
) IS 'Creates a tenant root row with tenant_id = id. Normalizes slug/email, validates format, blocks reserved slugs.';
"""

DROP_CREATE_TENANT_FUNCTION_SQL = """
DROP FUNCTION IF EXISTS platform.create_tenant(
    VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR
);
"""
