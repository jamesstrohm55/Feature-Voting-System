import type { FeatureResponse } from "../lib/api";
import { VoteButton } from "./VoteButton";

interface Props {
  feature: FeatureResponse;
  rank: number;
}

export function FeatureCard({ feature, rank }: Props) {
  const timeAgo = getTimeAgo(feature.created_at);

  return (
    <article className="flex items-start gap-4 rounded-xl border border-gray-100 bg-white p-4 shadow-sm transition-shadow hover:shadow-md">
      <VoteButton feature={feature} />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="shrink-0 text-xs font-medium text-gray-400">
            #{rank}
          </span>
          <h3 className="truncate text-sm font-semibold text-gray-900">
            {feature.title}
          </h3>
        </div>
        <p className="text-sm text-gray-600 line-clamp-2">
          {feature.description}
        </p>
        <div className="mt-2 flex items-center gap-3 text-xs text-gray-400">
          <span>{timeAgo}</span>
          {feature.is_own && (
            <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-indigo-600 font-medium">
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
