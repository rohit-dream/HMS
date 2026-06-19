export interface ErrorDetail {
  code: string;
  message: string;
  field?: string | null;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface ResponseMeta {
  request_id: string;
  timestamp: string;
  tenant_id?: string | null;
  pagination?: PaginationMeta | null;
}

export interface APIResponse<T> {
  data: T | null;
  meta: ResponseMeta;
  errors: ErrorDetail[] | null;
}

export interface HealthData {
  status: string;
  service?: string;
  version?: string;
  environment?: string;
}

export interface ReadinessData {
  status: string;
  checks: {
    database: string;
    redis: string;
  };
}
