import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

/** Fetches the ranked list of feature requests, optionally filtered by search term. */
export function useFeatures(search?: string) {
  return useQuery({
    queryKey: ["features", search ?? ""],
    queryFn: () => api.getFeatures(search),
  });
}
