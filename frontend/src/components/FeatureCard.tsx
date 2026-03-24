import { useState } from "react";
import type { FeatureResponse, FeatureStatus } from "../lib/api";
import { VoteButton } from "./VoteButton";
import { useAdmin } from "../hooks/useAdmin";

interface Props {
  feature: FeatureResponse;
  rank: number;
}

const STATUS_CONFIG: Record<FeatureStatus, { label: string; classes: string }> = {
  under_review: { label: "Under Review", classes: "bg-gray-100 text-gray-600" },
  planned:      { label: "Planned",      classes: "bg-blue-50 text-blue-600" },
  in_progress:  { label: "In Progress",  classes: "bg-amber-50 text-amber-700" },
  shipped:      { label: "Shipped",      classes: "bg-green-50 text-green-700" },
};

const STATUS_OPTIONS: { value: FeatureStatus; label: string }[] = [
  { value: "under_review", label: "Under Review" },
  { value: "planned", label: "Planned" },
  { value: "in_progress", label: "In Progress" },
  { value: "shipped", label: "Shipped" },
];

export function FeatureCard({ feature, rank }: Props) {
  const timeAgo = getTimeAgo(feature.created_at);
  const badge = STATUS_CONFIG[feature.status];
  const isStaff = feature.is_staff;
  const { updateStatus, deleteFeature, togglePin } = useAdmin();
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <article
      aria-label={`${feature.title} — ${feature.vote_count} votes`}
      className={`flex items-start gap-3 rounded-xl border bg-white p-4 shadow-sm transition-shadow duration-150 hover:shadow-md sm:gap-4 sm:p-5 ${
        feature.is_pinned
          ? "border-l-4 border-l-amber-400 border-t-gray-100 border-r-gray-100 border-b-gray-100"
          : "border-gray-100"
      }`}
    >
      <VoteButton feature={feature} />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="shrink-0 flex items-center justify-center h-5 w-5 rounded bg-slate-100 text-[10px] font-semibold text-slate-400">
            {rank}
          </span>
          <h3
            className="truncate text-sm font-semibold text-slate-900 sm:text-base"
            title={feature.title}
          >
            {feature.title}
          </h3>
          {!isStaff && badge && (
            <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium leading-tight ${badge.classes}`}>
              {badge.label}
            </span>
          )}
        </div>

        <p className="text-sm text-slate-600 line-clamp-2">
          {feature.description}
        </p>

        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400 sm:gap-3 sm:text-sm">
          <span>{feature.author_username}</span>
          <span>{timeAgo}</span>
          {feature.is_pinned && (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700 font-medium">
              <svg aria-hidden="true" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.562.562 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.562.562 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
              pinned
            </span>
          )}
          {feature.is_own && (
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-600 font-medium">
              <svg aria-hidden="true" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0" />
              </svg>
              yours
            </span>
          )}
        </div>

        {/* ── Staff controls ─────────────────────────────────── */}
        {isStaff && (
          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-3">
            {/* Status dropdown */}
            <select
              value={feature.status}
              onChange={(e) =>
                updateStatus.mutate({
                  id: feature.id,
                  status: e.target.value as FeatureStatus,
                })
              }
              aria-label="Change status"
              className="h-7 rounded border border-gray-200 bg-white px-2 text-xs text-slate-700 cursor-pointer focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/20"
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>

            {/* Pin toggle */}
            <button
              onClick={() => togglePin.mutate(feature.id)}
              title={feature.is_pinned ? "Unpin" : "Pin to top"}
              aria-label={feature.is_pinned ? "Unpin feature" : "Pin feature to top"}
              className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-xs font-medium transition-colors duration-150 cursor-pointer ${
                feature.is_pinned
                  ? "border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100"
                  : "border-gray-200 bg-white text-slate-500 hover:bg-gray-50"
              }`}
            >
              <svg aria-hidden="true" className="h-3.5 w-3.5" fill={feature.is_pinned ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.562.562 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.562.562 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
              </svg>
              {feature.is_pinned ? "Unpin" : "Pin"}
            </button>

            {/* Delete */}
            {!confirmDelete ? (
              <button
                onClick={() => setConfirmDelete(true)}
                aria-label="Delete feature"
                className="rounded border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-red-500 transition-colors duration-150 hover:bg-red-50 hover:border-red-200 cursor-pointer"
              >
                Delete
              </button>
            ) : (
              <span className="inline-flex items-center gap-1.5">
                <span className="text-xs text-slate-500">Are you sure?</span>
                <button
                  onClick={() => deleteFeature.mutate(feature.id)}
                  className="rounded bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700 cursor-pointer"
                >
                  Yes, delete
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="rounded border border-gray-200 px-2 py-1 text-xs font-medium text-slate-500 hover:bg-gray-50 cursor-pointer"
                >
                  Cancel
                </button>
              </span>
            )}
          </div>
        )}
      </div>
    </article>
  );
}

function getTimeAgo(dateStr: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
