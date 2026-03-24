import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { featureFormSchema, type FeatureFormData } from "../lib/schemas";

export function SubmitForm() {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [form, setForm] = useState<FeatureFormData>({ title: "", description: "" });
  const [errors, setErrors] = useState<Partial<Record<keyof FeatureFormData, string>>>({});

  const mutation = useMutation({
    mutationFn: api.createFeature,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["features"] });
      setForm({ title: "", description: "" });
      setErrors({});
      setIsOpen(false);
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const result = featureFormSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: typeof errors = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof FeatureFormData;
        fieldErrors[field] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }
    setErrors({});
    mutation.mutate(result.data);
  }

  if (!isOpen) {
    return (
      <div className="mt-6 mb-8">
        <button
          onClick={() => setIsOpen(true)}
          className="w-full rounded-xl border-2 border-dashed border-blue-200 bg-white px-6 py-4 text-blue-600 font-medium transition-colors duration-150 hover:border-blue-400 hover:bg-blue-50 cursor-pointer"
        >
          + Submit a Feature Request
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-6 mb-8 rounded-xl border border-blue-200 bg-white p-5 shadow-sm sm:p-6 md:p-8"
    >
      <h2 className="mb-4 text-base font-semibold text-slate-900">
        New Feature Request
      </h2>

      <div className="mb-4">
        <label htmlFor="title" className="mb-1.5 block text-sm font-medium text-slate-700">
          Title
        </label>
        <input
          id="title"
          type="text"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          placeholder="Short, descriptive title"
          aria-invalid={!!errors.title}
          aria-describedby={errors.title ? "title-error" : undefined}
          className="h-11 w-full rounded-lg border border-gray-300 px-3 text-sm text-slate-900 placeholder-gray-400 transition-colors duration-150 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          maxLength={200}
        />
        {errors.title && (
          <p id="title-error" role="alert" className="mt-1.5 text-xs text-red-600">
            {errors.title}
          </p>
        )}
      </div>

      <div className="mb-4">
        <label htmlFor="description" className="mb-1.5 block text-sm font-medium text-slate-700">
          Description
        </label>
        <textarea
          id="description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          placeholder="Why is this feature important? How would it work?"
          rows={3}
          aria-invalid={!!errors.description}
          aria-describedby={errors.description ? "desc-error" : undefined}
          className="w-full rounded-lg border border-gray-300 px-3 py-3 text-sm text-slate-900 placeholder-gray-400 transition-colors duration-150 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
          maxLength={2000}
        />
        {errors.description && (
          <p id="desc-error" role="alert" className="mt-1.5 text-xs text-red-600">
            {errors.description}
          </p>
        )}
      </div>

      {mutation.error && (
        <p role="alert" className="mb-3 text-sm text-red-600">
          {mutation.error instanceof Error ? mutation.error.message : "Failed to submit"}
        </p>
      )}

      <div className="flex gap-3 justify-end">
        <button
          type="button"
          onClick={() => {
            setIsOpen(false);
            setErrors({});
          }}
          className="rounded-lg px-4 py-2.5 text-sm font-medium text-slate-600 transition-colors duration-150 hover:bg-gray-100 cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors duration-150 hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {mutation.isPending ? "Submitting..." : "Submit"}
        </button>
      </div>
    </form>
  );
}
