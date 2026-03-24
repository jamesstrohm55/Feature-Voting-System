import type { FeatureResponse } from "../lib/api";
import { useVote } from "../hooks/useVote";

interface Props {
  feature: FeatureResponse;
}

export function VoteButton({ feature }: Props) {
  const { vote, unvote } = useVote();
  const isPending = vote.isPending || unvote.isPending;

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
      title={
        feature.is_own
          ? "You can't vote on your own feature"
          : feature.has_voted
            ? "Click to remove your vote"
            : "Click to upvote"
      }
      className={`flex shrink-0 flex-col items-center justify-center rounded-lg w-14 h-14 text-sm font-semibold transition-all cursor-pointer
        ${
          feature.is_own
            ? "border border-gray-100 bg-gray-50 text-gray-300 cursor-not-allowed"
            : feature.has_voted
              ? "border border-indigo-200 bg-indigo-50 text-indigo-600 hover:bg-indigo-100"
              : "border border-gray-200 bg-white text-gray-600 hover:border-indigo-300 hover:text-indigo-600"
        }
        ${isPending ? "opacity-50" : ""}
      `}
    >
      <svg
        className={`h-4 w-4 ${feature.has_voted ? "text-indigo-600" : ""}`}
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
