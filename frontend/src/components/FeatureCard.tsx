import type { FeatureResponse } from "../lib/api";
import { VoteButton } from "./VoteButton";

interface Props {
  feature: FeatureResponse;
  rank: number;
}

export function FeatureCard({ feature, rank }: Props) {
  const timeAgo = getTimeAgo(feature.created_at);

  return (
    <article
      aria-label={`${feature.title} — ${feature.vote_count} votes`}
      className="flex items-start gap-3 rounded-xl border border-gray-100 bg-white p-4 shadow-sm transition-shadow duration-150 hover:shadow-md sm:gap-4 sm:p-5"
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
        </div>
        <p className="text-sm text-slate-600 line-clamp-2">
          {feature.description}
        </p>
        <div className="mt-2 flex items-center gap-3 text-xs text-slate-400 sm:text-sm">
          <span>{timeAgo}</span>
          {feature.is_own && (
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-600 font-medium">
              <svg aria-hidden="true" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0" />
              </svg>
              yours
            </span>
          )}
        </div>
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
