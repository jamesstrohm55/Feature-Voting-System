import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type FeatureResponse } from "../lib/api";

/** Mutation hooks for voting and unvoting with optimistic updates. */
export function useVote() {
  const queryClient = useQueryClient();

  const vote = useMutation({
    mutationFn: api.vote,
    onMutate: async (featureId) => {
      await queryClient.cancelQueries({ queryKey: ["features"] });
      const previous = queryClient.getQueryData<FeatureResponse[]>(["features"]);

      queryClient.setQueryData<FeatureResponse[]>(["features"], (old) =>
        old?.map((f) =>
          f.id === featureId
            ? { ...f, vote_count: f.vote_count + 1, has_voted: true }
            : f
        )
      );

      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["features"], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });

  const unvote = useMutation({
    mutationFn: api.unvote,
    onMutate: async (featureId) => {
      await queryClient.cancelQueries({ queryKey: ["features"] });
      const previous = queryClient.getQueryData<FeatureResponse[]>(["features"]);

      queryClient.setQueryData<FeatureResponse[]>(["features"], (old) =>
        old?.map((f) =>
          f.id === featureId
            ? { ...f, vote_count: f.vote_count - 1, has_voted: false }
            : f
        )
      );

      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["features"], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["features"] });
    },
  });

  return { vote, unvote };
}
