export function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-indigo-100 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold text-sm">
          FV
        </div>
        <div>
          <h1 className="text-lg font-semibold text-gray-900 leading-tight">
            FeatureVote
          </h1>
          <p className="text-xs text-gray-500">
            Submit ideas &middot; Vote on what matters
          </p>
        </div>
      </div>
    </header>
  );
}
