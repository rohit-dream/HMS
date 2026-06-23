export type StaffStatus = "active" | "on_leave" | "terminated";

export interface StaffMember {
  id: string;
  tenant_id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  department_id: string | null;
  department_name: string | null;
  designation: string | null;
  status: StaffStatus;
  joining_date: string;
  leaving_date: string | null;
  location_id: string | null;
  is_doctor: boolean;
  user_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface StaffCreate {
  employee_code: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  department_id?: string;
  designation?: string;
  joining_date: string;
  leaving_date?: string;
  status?: StaffStatus;
  location_id?: string;
}

export interface StaffUpdate {
  employee_code?: string;
  first_name?: string;
  last_name?: string;
  email?: string | null;
  phone?: string | null;
  department_id?: string | null;
  designation?: string | null;
  joining_date?: string;
  leaving_date?: string | null;
  status?: StaffStatus;
  location_id?: string | null;
}
