import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type FeatureResponse, type FeatureStatus } from "../lib/api";

/** Admin mutation hooks with optimistic updates. */
export function useAdmin() {
  const qc = useQueryClient();

  function optimistic(
    updater: (old: FeatureResponse[]) => FeatureResponse[]
  ) {
    const previous: Record<string, FeatureResponse[] | undefined> = {};
    qc.getQueriesData<FeatureResponse[]>({ queryKey: ["features"] }).forEach(
      ([key, data]) => {
        previous[JSON.stringify(key)] = data;
        if (data) qc.setQueryData(key, updater(data));
      }
    );
    return previous;
  }

  function rollback(previous: Record<string, FeatureResponse[] | undefined>) {
    Object.entries(previous).forEach(([key, data]) => {
      if (data) qc.setQueryData(JSON.parse(key), data);
    });
  }

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: FeatureStatus }) =>
      api.updateStatus(id, status),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: ["features"] });
      const prev = optimistic((old) =>
        old.map((f) => (f.id === id ? { ...f, status } : f))
      );
      return { prev };
    },
    onError: (_err, _vars, ctx) => ctx && rollback(ctx.prev),
    onSettled: () => qc.invalidateQueries({ queryKey: ["features"] }),
  });

  const deleteFeature = useMutation({
    mutationFn: (id: string) => api.deleteFeature(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["features"] });
      const prev = optimistic((old) => old.filter((f) => f.id !== id));
      return { prev };
    },
    onError: (_err, _id, ctx) => ctx && rollback(ctx.prev),
    onSettled: () => qc.invalidateQueries({ queryKey: ["features"] }),
  });

  const togglePin = useMutation({
    mutationFn: (id: string) => api.togglePin(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["features"] });
      const prev = optimistic((old) =>
        old.map((f) => (f.id === id ? { ...f, is_pinned: !f.is_pinned } : f))
      );
      return { prev };
    },
    onError: (_err, _id, ctx) => ctx && rollback(ctx.prev),
    onSettled: () => qc.invalidateQueries({ queryKey: ["features"] }),
  });

  return { updateStatus, deleteFeature, togglePin };
}
