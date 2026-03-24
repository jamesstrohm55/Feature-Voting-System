import { z } from "zod";

export const featureStatusSchema = z.union([
  z.literal("under_review"),
  z.literal("planned"),
  z.literal("in_progress"),
  z.literal("shipped"),
]);

export type FeatureStatus = z.infer<typeof featureStatusSchema>;

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
