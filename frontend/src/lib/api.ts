import { getToken } from "./auth";

const BASE_URL = import.meta.env.PROD
  ? "https://feature-voting-system-production.up.railway.app/api"
  : "/api";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Token ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? "Something went wrong");
  }

  // 204 No Content has no body
  if (res.status === 204) return undefined as T;
  return res.json();
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface AuthResponse {
  token: string;
  user_id: number;
  username: string;
}

export const api = {
  register: (data: { username: string; password: string }) =>
    request<AuthResponse>("/auth/register/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { username: string; password: string }) =>
    request<AuthResponse>("/auth/login/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getFeatures: (search?: string) => {
    const params = search ? `?search=${encodeURIComponent(search)}` : "";
    return request<FeatureResponse[]>(`/features/${params}`);
  },

  createFeature: (data: { title: string; description: string }) =>
    request<FeatureResponse>("/features/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  vote: (featureId: string) =>
    request<VoteResponse>(`/features/${featureId}/vote/`, {
      method: "POST",
    }),

  unvote: (featureId: string) =>
    request<VoteResponse>(`/features/${featureId}/vote/`, {
      method: "DELETE",
    }),

  updateStatus: (featureId: string, status: FeatureStatus) =>
    request<FeatureResponse>(`/features/${featureId}/`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  deleteFeature: (featureId: string) =>
    request<void>(`/features/${featureId}/`, {
      method: "DELETE",
    }),

  togglePin: (featureId: string) =>
    request<{ is_pinned: boolean }>(`/features/${featureId}/pin/`, {
      method: "PATCH",
    }),
};

export type FeatureStatus = "under_review" | "planned" | "in_progress" | "shipped";

export interface FeatureResponse {
  id: string;
  title: string;
  description: string;
  author_username: string;
  status: FeatureStatus;
  is_pinned: boolean;
  vote_count: number;
  has_voted: boolean;
  is_own: boolean;
  is_staff: boolean;
  created_at: string;
}

export interface VoteResponse {
  vote_count: number;
  has_voted: boolean;
}
