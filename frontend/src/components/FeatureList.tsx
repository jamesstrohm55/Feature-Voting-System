import { useState } from "react";
import type { FeatureStatus } from "../lib/api";
import { useFeatures } from "../hooks/useFeatures";
import { FeatureCard } from "./FeatureCard";
import { EmptyState } from "./EmptyState";

type Filter = "all" | FeatureStatus;

const FILTERS: { value: Filter; label: string; active: string; inactive: string }[] = [
  { value: "all",          label: "All",          active: "bg-slate-800 text-white",        inactive: "bg-white text-slate-600 hover:bg-slate-50" },
  { value: "under_review", label: "Under Review",  active: "bg-gray-600 text-white",         inactive: "bg-white text-gray-600 hover:bg-gray-50" },
  { value: "planned",      label: "Planned",       active: "bg-blue-600 text-white",          inactive: "bg-white text-blue-600 hover:bg-blue-50" },
  { value: "in_progress",  label: "In Progress",   active: "bg-amber-600 text-white",         inactive: "bg-white text-amber-700 hover:bg-amber-50" },
  { value: "shipped",      label: "Shipped",        active: "bg-green-600 text-white",         inactive: "bg-white text-green-700 hover:bg-green-50" },
];

export function FeatureList() {
  const { data: features, isLoading, error } = useFeatures();
  const [filter, setFilter] = useState<Filter>("all");

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

  const filtered = filter === "all"
    ? features
    : features.filter((f) => f.status === filter);

  return (
    <div className="space-y-3" aria-live="polite">
      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filter by status">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            aria-pressed={filter === f.value}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors duration-150 cursor-pointer ${
              filter === f.value
                ? `${f.active} border-transparent`
                : `${f.inactive} border-gray-200`
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
        {filtered.length} feature request{filtered.length !== 1 && "s"}
        {filter !== "all" && ` · ${FILTERS.find((f) => f.value === filter)!.label}`}
      </h2>

      {filtered.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-200 bg-white p-8 text-center">
          <p className="text-sm text-slate-500">No features with this status.</p>
        </div>
      ) : (
        filtered.map((feature, index) => (
          <FeatureCard key={feature.id} feature={feature} rank={index + 1} />
        ))
      )}
    </div>
  );
}
