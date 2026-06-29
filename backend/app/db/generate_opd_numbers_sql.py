"""Canonical SQL for clinical OPD visit and prescription number generators."""

from __future__ import annotations

GENERATE_VISIT_NUMBER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION clinical.generate_visit_number(p_tenant_id UUID)
RETURNS VARCHAR(20)
LANGUAGE plpgsql
VOLATILE
SET search_path = clinical, public
AS $$
DECLARE
    v_ctx_tenant UUID;
    v_year       TEXT;
    v_seq        INTEGER;
    v_number     VARCHAR(20);
    v_prefix     TEXT;
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
    v_prefix := 'OPD-' || v_year || '-';
    v_pattern := '^OPD-' || v_year || '-([0-9]{5})$';

    PERFORM pg_advisory_xact_lock(hashtext(p_tenant_id::text || ':opd:' || v_year));

    SELECT COALESCE(
        MAX(substring(visit_number FROM v_pattern)::INTEGER),
        0
    ) + 1
    INTO v_seq
    FROM clinical.opd_visits
    WHERE tenant_id = p_tenant_id
      AND visit_number ~ v_pattern;

    IF v_seq > 99999 THEN
        RAISE EXCEPTION 'OPD visit sequence exhausted for tenant % in year %', p_tenant_id, v_year
            USING ERRCODE = '22023';
    END IF;

    v_number := v_prefix || lpad(v_seq::TEXT, 5, '0');
    RETURN v_number;
END;
$$;
"""

GENERATE_PRESCRIPTION_NUMBER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION clinical.generate_prescription_number(p_tenant_id UUID)
RETURNS VARCHAR(20)
LANGUAGE plpgsql
VOLATILE
SET search_path = clinical, public
AS $$
DECLARE
    v_ctx_tenant UUID;
    v_year       TEXT;
    v_seq        INTEGER;
    v_number     VARCHAR(20);
    v_prefix     TEXT;
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
    v_prefix := 'RX-' || v_year || '-';
    v_pattern := '^RX-' || v_year || '-([0-9]{5})$';

    PERFORM pg_advisory_xact_lock(hashtext(p_tenant_id::text || ':rx:' || v_year));

    SELECT COALESCE(
        MAX(substring(prescription_number FROM v_pattern)::INTEGER),
        0
    ) + 1
    INTO v_seq
    FROM clinical.opd_prescriptions
    WHERE tenant_id = p_tenant_id
      AND prescription_number ~ v_pattern;

    IF v_seq > 99999 THEN
        RAISE EXCEPTION 'Prescription sequence exhausted for tenant % in year %', p_tenant_id, v_year
            USING ERRCODE = '22023';
    END IF;

    v_number := v_prefix || lpad(v_seq::TEXT, 5, '0');
    RETURN v_number;
END;
$$;
"""

GENERATE_OPD_NUMBERS_GRANT_SQL = """
GRANT EXECUTE ON FUNCTION clinical.generate_visit_number(UUID) TO hms_app;
GRANT EXECUTE ON FUNCTION clinical.generate_prescription_number(UUID) TO hms_app;
"""
