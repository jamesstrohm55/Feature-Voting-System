import { useState, useEffect, useCallback } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { getToken, clearToken } from "./lib/auth";
import { AuthPage } from "./components/AuthPage";
import { Header } from "./components/Header";
import { SubmitForm } from "./components/SubmitForm";
import { FeatureList } from "./components/FeatureList";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      refetchOnWindowFocus: true,
    },
  },
});

export default function App() {
  const [isAuthed, setIsAuthed] = useState(() => !!getToken());
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput), 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const handleLogout = useCallback(() => {
    clearToken();
    queryClient.clear();
    setIsAuthed(false);
  }, []);

  if (!isAuthed) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthPage onAuth={() => setIsAuthed(true)} />
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-b from-slate-50 to-blue-50/30">
        <Header onLogout={handleLogout} />
        <main className="mx-auto max-w-2xl px-4 pb-16 md:px-6 lg:max-w-3xl lg:px-8">
          <SubmitForm />
          <div className="mb-4 mt-6">
            <div className="relative">
              <svg
                aria-hidden="true"
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              <input
                type="search"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search features..."
                aria-label="Search features"
                className="h-11 w-full rounded-lg border border-gray-200 bg-white pl-10 pr-3 text-sm text-slate-900 placeholder-slate-400 transition-colors duration-150 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>
          <FeatureList search={debouncedSearch} />
        </main>
      </div>
    </QueryClientProvider>
  );
}
