import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";

/** Fetches the ranked list of feature requests. */
export function useFeatures() {
  return useQuery({
    queryKey: ["features"],
    queryFn: api.getFeatures,
  });
}
