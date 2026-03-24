import { useFeatures } from "../hooks/useFeatures";
import { FeatureCard } from "./FeatureCard";
import { EmptyState } from "./EmptyState";

export function FeatureList() {
  const { data: features, isLoading, error } = useFeatures();

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-xl bg-white border border-gray-100"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
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
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
        {features.length} feature request{features.length !== 1 && "s"}
      </h2>
      {features.map((feature, index) => (
        <FeatureCard key={feature.id} feature={feature} rank={index + 1} />
      ))}
    </div>
  );
}
