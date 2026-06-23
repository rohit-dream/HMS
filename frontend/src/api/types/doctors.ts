export interface Doctor {
  id: string;
  tenant_id: string;
  staff_id: string;
  first_name: string;
  last_name: string;
  employee_code: string;
  registration_number: string | null;
  specialization: string;
  qualification: string | null;
  consultation_fee: string;
  follow_up_fee: string | null;
  department_id: string | null;
  department_name: string | null;
  bio: string | null;
  is_available: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface DoctorCreate {
  staff_id: string;
  registration_number?: string;
  specialization: string;
  qualification?: string;
  consultation_fee: string;
  follow_up_fee?: string;
  department_id?: string;
  bio?: string;
  is_available?: boolean;
}

export interface DoctorUpdate {
  registration_number?: string | null;
  specialization?: string;
  qualification?: string | null;
  consultation_fee?: string;
  follow_up_fee?: string | null;
  department_id?: string | null;
  bio?: string | null;
  is_available?: boolean;
}
