import { z } from "zod";
import { apiClient } from "@/services/apiClient";
const id = z.string().uuid(),
  stamp = z.string(),
  nullable = stamp.nullable().optional();
export const profile = z.object({
  id,
  username: z.string(),
  display_name: z.string(),
  avatar_url: nullable,
  created_at: stamp,
  updated_at: stamp,
});
export const preferences = z.object({
  user_id: id,
  onboarding_completed_at: nullable,
  timezone: z.string(),
  language: z.string(),
  daily_screen_goal_minutes: z.number().nullable().optional(),
  location_enabled: z.boolean(),
  screening_enabled: z.boolean(),
  notifications_enabled: z.boolean(),
  created_at: stamp,
  updated_at: stamp,
});
export const group = z.object({
  id,
  name: z.string(),
  description: nullable,
  created_by: id,
  visibility: z.enum(["private", "invite_only"]),
  created_at: stamp,
  updated_at: stamp,
  archived_at: nullable,
});
export const member = z.object({
  group_id: id,
  user_id: id,
  username: nullable,
  display_name: nullable,
  role: z.enum(["owner", "admin", "member"]),
  status: z.enum(["active", "left", "removed"]),
  joined_at: stamp,
});
export const friend = profile.pick({
  id: true,
  username: true,
  display_name: true,
  avatar_url: true,
});
export const activity = z.object({
  id,
  title: z.string(),
  description: z.string(),
  category: z.string(),
  visibility: z.enum(["personal", "group"]),
  status: z.enum([
    "draft",
    "published",
    "active",
    "awaiting_proof",
    "under_review",
    "completed",
    "cancelled",
    "expired",
    "rejected",
  ]),
  created_by: id,
  group_id: id.nullable().optional(),
  duration_minutes: z.number(),
  max_participants: z.number(),
  location_required: z.boolean(),
  proof_requirement: z.enum([
    "none",
    "photo",
    "group_confirmation",
    "photo_or_group_confirmation",
  ]),
  max_reward_points: z.number(),
  started_at: nullable,
  ended_at: nullable,
  published_at: nullable,
  created_at: stamp,
  updated_at: stamp,
});
export const participant = z.object({
  id,
  activity_id: id,
  user_id: id,
  status: z.enum([
    "joined",
    "active",
    "left",
    "awaiting_proof",
    "completed",
    "rejected",
  ]),
  joined_at: stamp,
  started_at: nullable,
  ended_at: nullable,
  completed_at: nullable,
  eligible_minutes: z.number(),
  points_awarded: z.number(),
});
export const record = z.object({
  id,
  user_id: id,
  usage_date: stamp,
  total_minutes: z.number(),
  social_minutes: z.number().nullable().optional(),
  category_breakdown: z.record(z.string(), z.number()).nullable().optional(),
  source: z.enum(["native", "manual", "import", "demo"]),
  created_at: stamp,
});
export const usage = z.object({
  total_screen_time_minutes: z.number(),
  daily_average_minutes: z.number(),
  social_time_minutes: z.number(),
  start_date: stamp,
  end_date: stamp,
  days_recorded: z.number(),
  daily_breakdown: record.array(),
});
export const coach = z.object({
  headline: z.string(),
  suggestion: z.string(),
  category: z.string(),
  recommended_activity_category: nullable,
});
export const activityMission = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  category: z.string(),
  duration_minutes: z.number(),
  proof_requirement: z.string(),
  max_reward_points: z.number(),
  tags: z.string().array(),
});
export const garden = z.object({
  id,
  garden_type: z.enum(["personal", "group"]),
  owner_user_id: id.nullable().optional(),
  owner_group_id: id.nullable().optional(),
  name: z.string(),
  points_balance: z.number(),
  growth_level: z.number(),
  created_at: stamp,
  updated_at: stamp,
});
export const catalog = z.object({
  id,
  name: z.string(),
  description: z.string(),
  item_type: z.enum(["seed", "plant", "pet", "decoration"]),
  price_points: z.number(),
  asset_key: z.string(),
  is_active: z.boolean(),
});
export const inventory = z.object({
  id,
  garden_id: id,
  catalog_item_id: id,
  catalog_item: catalog.nullable().optional(),
  quantity: z.number(),
  position_x: z.number().nullable().optional(),
  position_y: z.number().nullable().optional(),
  placed_at: nullable,
});
export const ledger = z.object({
  id,
  garden_id: id,
  user_id: id.nullable(),
  activity_participant_id: id.nullable().optional(),
  transaction_type: z.enum(["earn", "spend", "adjustment", "refund"]),
  amount: z.number(),
  reason: z.string(),
  created_at: stamp,
});
export const progression = z.object({
  user_id: id,
  level: z.number(),
  xp_current: z.number(),
  xp_to_next_level: z.number(),
  lifetime_xp: z.number(),
  completed_quests: z.number(),
  current_streak: z.number(),
  longest_streak: z.number(),
  garden_points: z.number(),
  achievements_unlocked: z.number(),
});
export const quest = z.object({
  id,
  code: z.string(),
  title: z.string(),
  description: z.string(),
  instructions: z.string(),
  category: z.string(),
  category_label: z.string(),
  difficulty: z.enum(["easy", "medium", "hard"]),
  estimated_duration_minutes: z.number(),
  xp_reward: z.number(),
  repeatability: z.string(),
  proof_requirement: z.string(),
  reflection_prompt: z.string().nullable().optional(),
  is_favorite: z.boolean(),
  active_instance_id: id.nullable().optional(),
  completion_count: z.number(),
});
export const questInstance = z.object({
  id,
  quest,
  activity_id: id,
  status: z.enum(["active", "completed", "abandoned"]),
  started_at: stamp,
  completed_at: nullable,
  abandoned_at: nullable,
  reflection: z.string().nullable().optional(),
  xp_claimed: z.boolean(),
});
export const questCompletion = z.object({
  instance_id: id,
  already_completed: z.boolean(),
  xp_awarded: z.number(),
  garden_points_awarded: z.number(),
  new_level: z.number(),
  xp_current: z.number(),
  xp_to_next_level: z.number(),
  unlocked_achievements: z.string().array(),
});
export const progressMission = z.object({
  id,
  code: z.string(),
  title: z.string(),
  description: z.string(),
  mission_type: z.enum(["daily", "weekly"]),
  current_progress: z.number(),
  target_value: z.number(),
  reward_xp: z.number(),
  status: z.string(),
  reward_claimed: z.boolean(),
  start_at: stamp,
  end_at: stamp,
});
export const achievement = z.object({
  code: z.string(), name: z.string(), description: z.string(),
  current_progress: z.number(), target_value: z.number(), reward_xp: z.number(),
  unlocked: z.boolean(), unlocked_at: nullable,
});
export const session = z.object({
  id,
  activity_id: id,
  participant_id: id,
  started_at: stamp,
  ended_at: nullable,
  status: z.enum(["active", "completed", "cancelled"]),
  created_at: stamp,
});
export const screening = z.object({
  engine: z.enum(["presidio", "none"]).default("none"),
  ner_enabled: z.boolean().default(false),
  status: z.string(),
  has_potential_pii: z.boolean(),
  has_harmful_content_indicators: z.boolean(),
  redacted_text: z.string(),
  limitations: z.string().array(),
  detections: z
    .object({
      entity_type: z.string(),
      start: z.number(),
      end: z.number(),
      score: z.number(),
      category: z.string(),
    })
    .array(),
});
export const success = z
  .object({ success: z.boolean(), message: nullable })
  .refine((value) => value.success, "The server did not confirm this action.");
export const proof = z.object({
  id,
  activity_id: id,
  participant_id: id,
  proof_type: z.string(),
  status: z.enum(["pending", "accepted", "rejected"]),
  submitted_at: stamp,
  reviewed_at: nullable,
});
export const invite = z.object({ invite_token: nullable, expires_at: stamp });
export const checkIn = z.object({
  check_in_id: id,
  captured_at: nullable,
  expires_at: nullable,
  accepted: z.boolean(),
  precision: z.string(),
});
export const upload = z.object({
  upload_url: z.string(),
  storage_key: z.string(),
  expires_at: stamp,
});
export async function request<S extends z.ZodType>(
  schema: S,
  path: string,
  method: "get" | "post" | "patch" | "delete" = "get",
  data?: unknown,
  options?: { timeout?: number },
): Promise<z.infer<S>> {
  const response = await apiClient.request<unknown>({
    url: path,
    method,
    data,
    ...options,
  });
  const envelope = z
    .object({ data: z.unknown(), request_id: z.string() })
    .safeParse(response.data);
  if (!envelope.success)
    throw new Error(
      "Unexpected server envelope. Please refresh or contact the team.",
    );
  const result = schema.safeParse(envelope.data.data);
  if (!result.success)
    throw new Error(
      "Unexpected server response. Please refresh or contact the team.",
    );
  return result.data;
}
export function message(error: unknown) {
  if (error instanceof z.ZodError)
    return error.issues.map((issue) => issue.message).join(" ");
  if (error instanceof Error) return error.message;
  const result = z.object({ message: z.string() }).safeParse(error);
  return result.success
    ? result.data.message
    : "Something went wrong. Please try again.";
}
export function minutes(value: number) {
  return `${Math.floor(value / 60)}h ${Math.round(value % 60)}m`;
}
export function utc(value: string) {
  return /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : `${value}Z`;
}
export function dateTime(value: string) {
  return new Date(utc(value)).toLocaleString();
}
export function localDate(timezone?: string) {
  const now = new Date();
  if (timezone) return new Intl.DateTimeFormat("en-CA", { timeZone: timezone, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}
export { z };
