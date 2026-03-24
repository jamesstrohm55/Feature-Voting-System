import { useFeatures } from "../hooks/useFeatures";
import { FeatureCard } from "./FeatureCard";
import { EmptyState } from "./EmptyState";

export function FeatureList() {
  const { data: features, isLoading, error } = useFeatures();

  if (isLoading) {
    return (
      <div className="space-y-3" aria-busy="true" aria-label="Loading features">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-xl bg-white border border-gray-100 p-4 sm:gap-4 sm:p-5"
          >
            <div className="h-14 w-14 shrink-0 animate-pulse rounded-lg bg-gray-100" />
            <div className="flex-1 space-y-2.5 py-1">
              <div className="h-4 w-3/4 animate-pulse rounded bg-gray-100" />
              <div className="h-3 w-full animate-pulse rounded bg-gray-50" />
              <div className="h-3 w-1/3 animate-pulse rounded bg-gray-50" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center" role="alert">
        <p className="text-sm text-red-600">
          Failed to load features. Is the backend running?
        </p>
      </div>
    );
  }

  if (!features || features.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-3" aria-live="polite">
      <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
        {features.length} feature request{features.length !== 1 && "s"}
      </h2>
      {features.map((feature, index) => (
        <FeatureCard key={feature.id} feature={feature} rank={index + 1} />
      ))}
    </div>
  );
}
