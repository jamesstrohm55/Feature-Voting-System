import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { setToken } from "../lib/auth";
import { authFormSchema, type AuthFormData } from "../lib/schemas";

interface Props {
  onAuth: () => void;
}

type Tab = "login" | "register";

export function AuthPage({ onAuth }: Props) {
  const [tab, setTab] = useState<Tab>("login");
  const [form, setForm] = useState<AuthFormData>({ username: "", password: "" });
  const [errors, setErrors] = useState<Partial<Record<keyof AuthFormData, string>>>({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError("");

    const result = authFormSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: typeof errors = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof AuthFormData;
        fieldErrors[field] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    setLoading(true);

    try {
      const fn = tab === "login" ? api.login : api.register;
      const data = await fn(result.data);
      setToken(data.token, { user_id: data.user_id, username: data.username });
      onAuth();
    } catch (err) {
      setApiError(
        err instanceof ApiError ? err.message : "Something went wrong"
      );
    } finally {
      setLoading(false);
    }
  }

  function switchTab(next: Tab) {
    setTab(next);
    setErrors({});
    setApiError("");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-50 to-blue-50/30 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-lg">
            FV
          </div>
          <h1 className="text-xl font-semibold text-slate-900">FeatureVote</h1>
          <p className="mt-1 text-sm text-slate-500">
            Submit ideas &middot; Vote on what matters
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
          {/* Tabs */}
          <div className="flex border-b border-gray-100">
            {(["login", "register"] as const).map((t) => (
              <button
                key={t}
                onClick={() => switchTab(t)}
                className={`flex-1 py-3 text-sm font-medium transition-colors duration-150 cursor-pointer ${
                  tab === t
                    ? "text-blue-600 border-b-2 border-blue-600"
                    : "text-slate-400 hover:text-slate-600"
                }`}
              >
                {t === "login" ? "Log In" : "Register"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-slate-700">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                autoComplete="username"
                aria-invalid={!!errors.username}
                className="h-11 w-full rounded-lg border border-gray-300 px-3 text-sm text-slate-900 placeholder-slate-400 transition-colors duration-150 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              {errors.username && (
                <p role="alert" className="mt-1 text-xs text-red-600">{errors.username}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                autoComplete={tab === "login" ? "current-password" : "new-password"}
                aria-invalid={!!errors.password}
                className="h-11 w-full rounded-lg border border-gray-300 px-3 text-sm text-slate-900 placeholder-slate-400 transition-colors duration-150 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
              {errors.password && (
                <p role="alert" className="mt-1 text-xs text-red-600">{errors.password}</p>
              )}
            </div>

            {apiError && (
              <p role="alert" className="text-sm text-red-600">{apiError}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="h-11 w-full rounded-lg bg-blue-600 text-sm font-medium text-white transition-colors duration-150 hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
            >
              {loading
                ? "Please wait..."
                : tab === "login"
                  ? "Log In"
                  : "Create Account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
