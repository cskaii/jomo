export interface DetectionItem {
  entity_type: string;
  start: number;
  end: number;
  score: number;
  category: string;
}

export interface ScreenTextResponse {
  status: string;
  has_potential_pii: boolean;
  has_harmful_content_indicators: boolean;
  detections: DetectionItem[];
  redacted_text: string;
  limitations: string[];
}

export interface WellbeingRecommendation {
  headline: string;
  suggestion: string;
  category: string;
  recommended_activity_category?: string | null;
}

export interface MissionRecommendation {
  id: string;
  title: string;
  description: string;
  category: string;
  duration_minutes: number;
  proof_requirement: string;
  max_reward_points: number;
  tags: string[];
}
