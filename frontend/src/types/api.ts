export interface ResponseEnvelope<T> {
  data: T;
  request_id: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ErrorEnvelope {
  error: ApiErrorDetail;
  request_id: string;
}

export interface SuccessStatus {
  success: boolean;
  message?: string;
}
