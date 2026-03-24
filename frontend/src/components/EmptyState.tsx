interface Props {
  heading?: string;
  message?: string;
}

export function EmptyState({
  heading = "No features yet",
  message = "Be the first to submit a feature request!",
}: Props) {
  return (
    <div className="rounded-xl border-2 border-dashed border-gray-200 bg-white p-8 text-center sm:p-12">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-50">
        <svg
          aria-hidden="true"
          className="h-6 w-6 text-blue-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-slate-900">{heading}</h3>
      <p className="mt-1 text-sm text-slate-500">{message}</p>
    </div>
  );
}
