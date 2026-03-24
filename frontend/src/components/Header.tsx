export function Header() {
  return (
    <header
      role="banner"
      aria-label="FeatureVote"
      className="sticky top-0 z-10 border-b border-blue-100 bg-white/80 backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-2xl items-center gap-3 px-4 py-4 md:px-6 lg:max-w-3xl lg:px-8">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-sm">
          FV
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-900 leading-tight">
            FeatureVote
          </h1>
          <p className="text-xs text-slate-500 sm:text-sm">
            Submit ideas &middot; Vote on what matters
          </p>
        </div>
      </div>
    </header>
  );
}
