"""Canonical SQL for core.generate_mrn() — per-tenant {prefix}-YYYY-NNNNN generator."""

from __future__ import annotations

GENERATE_MRN_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION core.generate_mrn(p_tenant_id UUID)
RETURNS VARCHAR(20)
LANGUAGE plpgsql
VOLATILE
SET search_path = core, platform, public
AS $$
DECLARE
    v_ctx_tenant UUID;
    v_year       TEXT;
    v_seq        INTEGER;
    v_mrn        VARCHAR(20);
    v_prefix     TEXT;
    v_label      TEXT;
    v_pattern    TEXT;
BEGIN
    IF p_tenant_id IS NULL THEN
        RAISE EXCEPTION 'tenant_id is required' USING ERRCODE = '22023';
    END IF;

    v_ctx_tenant := NULLIF(current_setting('app.tenant_id', true), '')::uuid;
    IF v_ctx_tenant IS NOT NULL AND v_ctx_tenant IS DISTINCT FROM p_tenant_id THEN
        RAISE EXCEPTION 'tenant_id does not match session context'
            USING ERRCODE = '42501';
    END IF;

    v_year := to_char(CURRENT_DATE, 'YYYY');

    SELECT COALESCE(NULLIF(trim(setting_value->>'mrn_prefix'), ''), 'MRN')
    INTO v_label
    FROM platform.tenant_settings
    WHERE tenant_id = p_tenant_id
      AND setting_key = 'clinical'
      AND deleted_at IS NULL
    LIMIT 1;

    IF v_label IS NULL THEN
        v_label := 'MRN';
    END IF;

    v_prefix := v_label || '-' || v_year || '-';
    v_pattern := '^' || v_label || '-' || v_year || '-([0-9]{5})$';

    PERFORM pg_advisory_xact_lock(hashtext(p_tenant_id::text || ':' || v_year || ':' || v_label));

    SELECT COALESCE(
        MAX(substring(mrn FROM v_pattern)::INTEGER),
        0
    ) + 1
    INTO v_seq
    FROM core.patients
    WHERE tenant_id = p_tenant_id
      AND mrn ~ v_pattern;

    IF v_seq > 99999 THEN
        RAISE EXCEPTION 'MRN sequence exhausted for tenant % in year %', p_tenant_id, v_year
            USING ERRCODE = '22023';
    END IF;

    v_mrn := v_prefix || lpad(v_seq::TEXT, 5, '0');
    RETURN v_mrn;
END;
$$;
"""

GENERATE_MRN_GRANT_SQL = """
GRANT EXECUTE ON FUNCTION core.generate_mrn(UUID) TO hms_app;
"""
