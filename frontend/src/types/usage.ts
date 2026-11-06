import { UsageSource } from "@/types/enums";

export interface UsageRecord {
  id: string;
  user_id: string;
  usage_date: string;
  total_minutes: number;
  social_minutes?: number | null;
  category_breakdown?: Record<string, number> | null;
  source: UsageSource;
  created_at: string;
}

export interface UsageSummary {
  total_screen_time_minutes: int;
  daily_average_minutes: int;
  social_time_minutes: int;
  start_date: string;
  end_date: string;
  days_recorded: number;
  daily_breakdown: UsageRecord[];
}

type int = number;
