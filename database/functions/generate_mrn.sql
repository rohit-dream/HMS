-- Per-tenant MRN generator: MRN-YYYY-NNNNN (applied via Alembic 022_generate_mrn_function).
-- Requires: core.patients (020_patient_tables).

CREATE OR REPLACE FUNCTION core.generate_mrn(p_tenant_id UUID)
RETURNS VARCHAR(20)
LANGUAGE plpgsql
VOLATILE
SET search_path = core, public
AS $$
DECLARE
    v_ctx_tenant UUID;
    v_year       TEXT;
    v_seq        INTEGER;
    v_mrn        VARCHAR(20);
    v_prefix     TEXT;
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
    v_prefix := 'MRN-' || v_year || '-';

    PERFORM pg_advisory_xact_lock(hashtext(p_tenant_id::text || ':' || v_year));

    SELECT COALESCE(
        MAX(
            substring(mrn FROM '^MRN-' || v_year || '-([0-9]{5})$')::INTEGER
        ),
        0
    ) + 1
    INTO v_seq
    FROM core.patients
    WHERE tenant_id = p_tenant_id
      AND mrn ~ ('^MRN-' || v_year || '-[0-9]{5}$');

    IF v_seq > 99999 THEN
        RAISE EXCEPTION 'MRN sequence exhausted for tenant % in year %', p_tenant_id, v_year
            USING ERRCODE = '22023';
    END IF;

    v_mrn := v_prefix || lpad(v_seq::TEXT, 5, '0');
    RETURN v_mrn;
END;
$$;

GRANT EXECUTE ON FUNCTION core.generate_mrn(UUID) TO hms_app;
