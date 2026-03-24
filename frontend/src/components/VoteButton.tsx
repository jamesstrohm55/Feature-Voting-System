import type { FeatureResponse } from "../lib/api";
import { useVote } from "../hooks/useVote";

interface Props {
  feature: FeatureResponse;
}

export function VoteButton({ feature }: Props) {
  const { vote, unvote } = useVote();
  const isPending = vote.isPending || unvote.isPending;

  const label = feature.is_own
    ? `${feature.title}, ${feature.vote_count} votes, your submission`
    : feature.has_voted
      ? `Remove vote from ${feature.title}, currently ${feature.vote_count} votes`
      : `Upvote ${feature.title}, currently ${feature.vote_count} votes`;

  function handleClick() {
    if (isPending || feature.is_own) return;
    if (feature.has_voted) {
      unvote.mutate(feature.id);
    } else {
      vote.mutate(feature.id);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={feature.is_own || isPending}
      aria-label={label}
      aria-pressed={feature.has_voted}
      className={`flex shrink-0 flex-col items-center justify-center rounded-lg w-14 h-14 text-sm font-semibold transition-colors duration-150 cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
        ${
          feature.is_own
            ? "border border-gray-100 bg-gray-50 text-gray-300 cursor-not-allowed"
            : feature.has_voted
              ? "border border-blue-200 bg-blue-50 text-blue-600 hover:bg-blue-100"
              : "border border-gray-200 bg-white text-slate-600 hover:border-blue-300 hover:text-blue-600"
        }
        ${isPending ? "opacity-50" : ""}
      `}
    >
      <svg
        aria-hidden="true"
        className={`h-4 w-4 ${feature.has_voted ? "text-blue-600" : ""}`}
        fill={feature.has_voted ? "currentColor" : "none"}
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
      </svg>
      <span>{feature.vote_count}</span>
    </button>
  );
}
