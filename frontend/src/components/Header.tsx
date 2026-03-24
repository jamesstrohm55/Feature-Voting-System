import { getUser } from "../lib/auth";

interface Props {
  onLogout: () => void;
}

export function Header({ onLogout }: Props) {
  const user = getUser();

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
        <div className="flex-1">
          <h1 className="text-lg font-semibold text-slate-900 leading-tight">
            FeatureVote
          </h1>
          <p className="text-xs text-slate-500 sm:text-sm">
            Submit ideas &middot; Vote on what matters
          </p>
        </div>
        {user && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{user.username}</span>
            <button
              onClick={onLogout}
              className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors duration-150 hover:bg-gray-50 cursor-pointer"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
