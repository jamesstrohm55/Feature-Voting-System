import { z } from "zod";

export const featureStatusSchema = z.union([
  z.literal("under_review"),
  z.literal("planned"),
  z.literal("in_progress"),
  z.literal("shipped"),
]);

export type FeatureStatus = z.infer<typeof featureStatusSchema>;

export const featureResponseSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  author_username: z.string(),
  status: featureStatusSchema,
  is_pinned: z.boolean(),
  vote_count: z.number(),
  has_voted: z.boolean(),
  is_own: z.boolean(),
  is_staff: z.boolean(),
  created_at: z.string(),
});

export type FeatureResponseData = z.infer<typeof featureResponseSchema>;

/** Client-side validation schema for the feature submission form. */
export const featureFormSchema = z.object({
  title: z
    .string()
    .min(3, "Title must be at least 3 characters")
    .max(200, "Title must be 200 characters or fewer"),
  description: z
    .string()
    .min(10, "Description must be at least 10 characters")
    .max(2000, "Description must be 2000 characters or fewer"),
});

export type FeatureFormData = z.infer<typeof featureFormSchema>;

export const authFormSchema = z.object({
  username: z
    .string()
    .min(1, "Username is required")
    .max(150, "Username must be 150 characters or fewer"),
  password: z
    .string()
    .min(6, "Password must be at least 6 characters"),
});

export type AuthFormData = z.infer<typeof authFormSchema>;
