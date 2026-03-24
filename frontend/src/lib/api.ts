import { getSessionId } from "./session";

const BASE_URL = "/api";

/**
 * Thin fetch wrapper that injects the X-Session-Id header
 * and handles JSON parsing + error status codes.
 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Session-Id": getSessionId(),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? "Something went wrong");
  }

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

export const api = {
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
};

export type FeatureStatus = "under_review" | "planned" | "in_progress" | "shipped";

export interface FeatureResponse {
  id: string;
  title: string;
  description: string;
  author_session_id: string;
  status: FeatureStatus;
  vote_count: number;
  has_voted: boolean;
  is_own: boolean;
  created_at: string;
}

export interface VoteResponse {
  vote_count: number;
  has_voted: boolean;
}
