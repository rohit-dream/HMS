export interface Department {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  head_staff_id: string | null;
  location_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface DepartmentCreate {
  name: string;
  code: string;
  head_staff_id?: string;
  location_id?: string;
  is_active?: boolean;
}

export interface DepartmentUpdate {
  name?: string;
  code?: string;
  head_staff_id?: string | null;
  location_id?: string | null;
  is_active?: boolean;
}
