import { ActivityStatus, ParticipantStatus, ActivityVisibility, ProofType } from "@/types/enums";

export interface Activity {
  id: string;
  title: string;
  description: string;
  category: string;
  visibility: ActivityVisibility;
  status: ActivityStatus;
  created_by: string;
  group_id?: string | null;
  duration_minutes: number;
  max_participants: number;
  location_required: boolean;
  proof_requirement: ProofType;
  max_reward_points: number;
  published_at?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ActivityParticipant {
  id: string;
  activity_id: string;
  user_id: string;
  status: ParticipantStatus;
  joined_at: string;
  started_at?: string | null;
  ended_at?: string | null;
  eligible_minutes: number;
  points_awarded: number;
  completed_at?: string | null;
}
