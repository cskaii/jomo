export interface UserProfile {
  id: string;
  username: string;
  display_name: string;
  avatar_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  user_id: string;
  timezone: string;
  language: string;
  daily_screen_goal_minutes?: number | null;
  location_enabled: boolean;
  screening_enabled: boolean;
  notifications_enabled: boolean;
  created_at: string;
  updated_at: string;
}
