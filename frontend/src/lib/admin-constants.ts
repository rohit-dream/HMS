/** Tenant-scoped roles available for assignment (excludes platform_admin). */
export const TENANT_ROLE_OPTIONS = [
  { code: "hospital_owner", label: "Hospital Owner" },
  { code: "hospital_admin", label: "Hospital Admin" },
  { code: "doctor", label: "Doctor" },
  { code: "nurse", label: "Nurse" },
  { code: "receptionist", label: "Receptionist" },
  { code: "pharmacist", label: "Pharmacist" },
  { code: "lab_technician", label: "Lab Technician" },
  { code: "accountant", label: "Accountant" },
] as const;

export const DATE_FORMAT_OPTIONS = ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"] as const;
