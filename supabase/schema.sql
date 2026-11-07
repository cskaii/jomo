-- JOMO: fresh database only. No application data is inserted.
-- alembic_version contains migration bookkeeping only.
BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> db98869da4be

CREATE TABLE garden_catalog_items (
    id UUID NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    description TEXT NOT NULL, 
    item_type VARCHAR(30) NOT NULL, 
    price_points INTEGER NOT NULL, 
    asset_key TEXT NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE users (
    id UUID NOT NULL, 
    username VARCHAR(30) NOT NULL, 
    display_name VARCHAR(80) NOT NULL, 
    avatar_url TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE consent_records (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    purpose VARCHAR(60) NOT NULL, 
    policy_version VARCHAR(30) NOT NULL, 
    granted BOOLEAN NOT NULL, 
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_consent_records_user_id ON consent_records (user_id);

CREATE TABLE friend_requests (
    id UUID NOT NULL, 
    sender_id UUID NOT NULL, 
    receiver_id UUID NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    responded_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT check_friend_request_status CHECK (status IN ('pending', 'accepted', 'declined', 'cancelled')), 
    CONSTRAINT check_friend_request_distinct CHECK (sender_id <> receiver_id), 
    FOREIGN KEY(receiver_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(sender_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_friend_requests_receiver_id ON friend_requests (receiver_id);

CREATE INDEX ix_friend_requests_sender_id ON friend_requests (sender_id);

CREATE TABLE friendships (
    id UUID NOT NULL, 
    user_low_id UUID NOT NULL, 
    user_high_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_friendship_ordering CHECK (user_low_id < user_high_id), 
    FOREIGN KEY(user_high_id) REFERENCES users (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_low_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_friendships_users UNIQUE (user_low_id, user_high_id)
);

CREATE INDEX ix_friendships_user_high_id ON friendships (user_high_id);

CREATE INDEX ix_friendships_user_low_id ON friendships (user_low_id);

CREATE TABLE groups (
    id UUID NOT NULL, 
    name VARCHAR(80) NOT NULL, 
    description TEXT, 
    created_by UUID NOT NULL, 
    visibility VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    archived_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT check_group_visibility CHECK (visibility IN ('private', 'invite_only')), 
    FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_groups_created_by ON groups (created_by);

CREATE TABLE notifications (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    type VARCHAR(40) NOT NULL, 
    title VARCHAR(120) NOT NULL, 
    body TEXT NOT NULL, 
    payload JSON, 
    read_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user_read ON notifications (user_id, read_at, created_at);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE screening_events (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    screening_type VARCHAR(30) NOT NULL, 
    source VARCHAR(30) NOT NULL, 
    detected_categories JSON, 
    result_status VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_screening_events_user_id ON screening_events (user_id);

CREATE TABLE usage_summaries (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    usage_date DATE NOT NULL, 
    total_minutes INTEGER NOT NULL, 
    social_minutes INTEGER, 
    category_breakdown JSON, 
    source VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_usage_summaries_user_date_source UNIQUE (user_id, usage_date, source)
);

CREATE INDEX ix_usage_summaries_usage_date ON usage_summaries (usage_date);

CREATE INDEX ix_usage_summaries_user_id ON usage_summaries (user_id);

CREATE TABLE user_preferences (
    user_id UUID NOT NULL, 
    timezone VARCHAR(64) NOT NULL, 
    language VARCHAR(10) NOT NULL, 
    daily_screen_goal_minutes INTEGER, 
    location_enabled BOOLEAN NOT NULL, 
    screening_enabled BOOLEAN NOT NULL, 
    notifications_enabled BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (user_id), 
    CONSTRAINT check_daily_screen_goal_minutes CHECK (daily_screen_goal_minutes IS NULL OR daily_screen_goal_minutes BETWEEN 1 AND 1440), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE activities (
    id UUID NOT NULL, 
    created_by UUID NOT NULL, 
    group_id UUID, 
    title VARCHAR(120) NOT NULL, 
    description TEXT NOT NULL, 
    category VARCHAR(40) NOT NULL, 
    visibility VARCHAR(20) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    duration_minutes INTEGER NOT NULL, 
    max_participants INTEGER NOT NULL, 
    location_required BOOLEAN NOT NULL, 
    proof_requirement VARCHAR(40) NOT NULL, 
    points_per_minute NUMERIC(6, 2), 
    max_reward_points INTEGER NOT NULL, 
    published_at TIMESTAMP WITH TIME ZONE, 
    started_at TIMESTAMP WITH TIME ZONE, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_activity_visibility_group_match CHECK ((visibility = 'personal' AND group_id IS NULL) OR (visibility = 'group' AND group_id IS NOT NULL)), 
    CONSTRAINT check_activity_visibility CHECK (visibility IN ('personal', 'group')), 
    CONSTRAINT check_activity_duration CHECK (duration_minutes BETWEEN 1 AND 480), 
    CONSTRAINT check_activity_max_participants CHECK (max_participants BETWEEN 1 AND 100), 
    CONSTRAINT check_activity_max_reward_points CHECK (max_reward_points BETWEEN 0 AND 10000), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(group_id) REFERENCES groups (id)
);

CREATE INDEX idx_activities_creator ON activities (created_by, created_at);

CREATE INDEX idx_activities_group_status ON activities (group_id, status, created_at);

CREATE INDEX ix_activities_created_by ON activities (created_by);

CREATE INDEX ix_activities_group_id ON activities (group_id);

CREATE TABLE gardens (
    id UUID NOT NULL, 
    garden_type VARCHAR(20) NOT NULL, 
    owner_user_id UUID, 
    owner_group_id UUID, 
    name VARCHAR(80) NOT NULL, 
    points_balance INTEGER NOT NULL, 
    growth_level INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_garden_owner_validity CHECK ((garden_type = 'personal' AND owner_user_id IS NOT NULL AND owner_group_id IS NULL) OR (garden_type = 'group' AND owner_user_id IS NULL AND owner_group_id IS NOT NULL)), 
    CONSTRAINT check_garden_growth_level_positive CHECK (growth_level >= 1), 
    CONSTRAINT check_garden_points_balance_positive CHECK (points_balance >= 0), 
    FOREIGN KEY(owner_group_id) REFERENCES groups (id) ON DELETE CASCADE, 
    FOREIGN KEY(owner_user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_gardens_owner_group_id ON gardens (owner_group_id);

CREATE INDEX ix_gardens_owner_user_id ON gardens (owner_user_id);

CREATE TABLE group_invites (
    id UUID NOT NULL, 
    group_id UUID NOT NULL, 
    created_by UUID NOT NULL, 
    token_hash VARCHAR(128) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    max_uses INTEGER, 
    uses_count INTEGER NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(group_id) REFERENCES groups (id) ON DELETE CASCADE, 
    UNIQUE (token_hash)
);

CREATE INDEX ix_group_invites_group_id ON group_invites (group_id);

CREATE TABLE group_members (
    group_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    left_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (group_id, user_id), 
    CONSTRAINT check_group_member_role CHECK (role IN ('owner', 'admin', 'member')), 
    CONSTRAINT check_group_member_status CHECK (status IN ('active', 'left', 'removed')), 
    FOREIGN KEY(group_id) REFERENCES groups (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX idx_group_members_group ON group_members (group_id, status);

CREATE INDEX idx_group_members_user ON group_members (user_id, status);

CREATE TABLE activity_participants (
    id UUID NOT NULL, 
    activity_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    joined_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    eligible_minutes INTEGER NOT NULL, 
    points_awarded INTEGER NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT check_participant_eligible_minutes CHECK (eligible_minutes >= 0), 
    CONSTRAINT check_participant_points_awarded CHECK (points_awarded >= 0), 
    FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    CONSTRAINT uq_activity_participants_user UNIQUE (activity_id, user_id)
);

CREATE INDEX idx_activity_participants_activity ON activity_participants (activity_id, status);

CREATE INDEX idx_activity_participants_user ON activity_participants (user_id, status);

CREATE INDEX ix_activity_participants_activity_id ON activity_participants (activity_id);

CREATE INDEX ix_activity_participants_user_id ON activity_participants (user_id);

CREATE TABLE garden_items (
    id UUID NOT NULL, 
    garden_id UUID NOT NULL, 
    catalog_item_id UUID NOT NULL, 
    quantity INTEGER NOT NULL, 
    position_x NUMERIC(8, 2), 
    position_y NUMERIC(8, 2), 
    placed_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(catalog_item_id) REFERENCES garden_catalog_items (id), 
    FOREIGN KEY(garden_id) REFERENCES gardens (id) ON DELETE CASCADE
);

CREATE INDEX ix_garden_items_catalog_item_id ON garden_items (catalog_item_id);

CREATE INDEX ix_garden_items_garden_id ON garden_items (garden_id);

CREATE TABLE activity_check_ins (
    id UUID NOT NULL, 
    activity_id UUID NOT NULL, 
    participant_id UUID NOT NULL, 
    latitude NUMERIC(9, 6), 
    longitude NUMERIC(9, 6), 
    accuracy_meters NUMERIC(8, 2), 
    precision_level VARCHAR(20) NOT NULL, 
    consent_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    FOREIGN KEY(participant_id) REFERENCES activity_participants (id) ON DELETE CASCADE
);

CREATE INDEX ix_activity_check_ins_activity_id ON activity_check_ins (activity_id);

CREATE INDEX ix_activity_check_ins_participant_id ON activity_check_ins (participant_id);

CREATE TABLE focus_sessions (
    id UUID NOT NULL, 
    activity_id UUID NOT NULL, 
    participant_id UUID NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    status VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_focus_session_status CHECK (status IN ('active', 'completed', 'cancelled')), 
    FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    FOREIGN KEY(participant_id) REFERENCES activity_participants (id) ON DELETE CASCADE
);

CREATE INDEX ix_focus_sessions_activity_id ON focus_sessions (activity_id);

CREATE INDEX ix_focus_sessions_participant_id ON focus_sessions (participant_id);

CREATE TABLE point_transactions (
    id UUID NOT NULL, 
    garden_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    activity_participant_id UUID, 
    transaction_type VARCHAR(20) NOT NULL, 
    amount INTEGER NOT NULL, 
    reason VARCHAR(100) NOT NULL, 
    idempotency_key VARCHAR(150) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_transaction_type CHECK (transaction_type IN ('earn', 'spend', 'refund', 'adjustment')), 
    CONSTRAINT check_transaction_amount_nonzero CHECK (amount <> 0), 
    FOREIGN KEY(activity_participant_id) REFERENCES activity_participants (id), 
    FOREIGN KEY(garden_id) REFERENCES gardens (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX idx_point_transactions_garden_date ON point_transactions (garden_id, created_at);

CREATE INDEX idx_point_transactions_user_date ON point_transactions (user_id, created_at);

CREATE INDEX ix_point_transactions_activity_participant_id ON point_transactions (activity_participant_id);

CREATE INDEX ix_point_transactions_garden_id ON point_transactions (garden_id);

CREATE UNIQUE INDEX ix_point_transactions_idempotency_key ON point_transactions (idempotency_key);

CREATE INDEX ix_point_transactions_user_id ON point_transactions (user_id);

CREATE TABLE proof_submissions (
    id UUID NOT NULL, 
    activity_id UUID NOT NULL, 
    participant_id UUID NOT NULL, 
    proof_type VARCHAR(30) NOT NULL, 
    storage_key TEXT, 
    mime_type VARCHAR(100), 
    file_size_bytes BIGINT, 
    status VARCHAR(20) NOT NULL, 
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    reviewed_at TIMESTAMP WITH TIME ZONE, 
    reviewed_by UUID, 
    retention_until TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT check_proof_type CHECK (proof_type IN ('photo', 'group_confirmation')), 
    CONSTRAINT check_proof_status CHECK (status IN ('pending', 'accepted', 'rejected')), 
    FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    FOREIGN KEY(participant_id) REFERENCES activity_participants (id) ON DELETE CASCADE, 
    FOREIGN KEY(reviewed_by) REFERENCES users (id)
);

CREATE INDEX idx_proof_submissions_activity ON proof_submissions (activity_id, status);

CREATE INDEX ix_proof_submissions_activity_id ON proof_submissions (activity_id);

CREATE INDEX ix_proof_submissions_participant_id ON proof_submissions (participant_id);

CREATE TABLE proof_confirmations (
    id UUID NOT NULL, 
    proof_id UUID NOT NULL, 
    confirmed_by UUID NOT NULL, 
    decision VARCHAR(20) NOT NULL, 
    comment VARCHAR(300), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_confirmation_decision CHECK (decision IN ('confirm', 'reject')), 
    FOREIGN KEY(confirmed_by) REFERENCES users (id), 
    FOREIGN KEY(proof_id) REFERENCES proof_submissions (id) ON DELETE CASCADE, 
    CONSTRAINT uq_proof_confirmations_user UNIQUE (proof_id, confirmed_by)
);

CREATE INDEX ix_proof_confirmations_proof_id ON proof_confirmations (proof_id);

INSERT INTO alembic_version (version_num) VALUES ('db98869da4be') RETURNING alembic_version.version_num;

-- Running upgrade db98869da4be -> a1f4c2d9e710

CREATE TABLE user_progression (
    user_id UUID NOT NULL, 
    level INTEGER NOT NULL, 
    xp_current INTEGER NOT NULL, 
    lifetime_xp INTEGER NOT NULL, 
    completed_quests INTEGER NOT NULL, 
    current_streak INTEGER NOT NULL, 
    longest_streak INTEGER NOT NULL, 
    last_completion_date DATE, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (user_id), 
    CONSTRAINT check_progression_level CHECK (level >= 1), 
    CONSTRAINT check_progression_xp CHECK (xp_current >= 0 AND lifetime_xp >= 0), 
    CONSTRAINT check_completed_quests CHECK (completed_quests >= 0), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE quests (
    id UUID NOT NULL, 
    code VARCHAR(12) NOT NULL, 
    title VARCHAR(120) NOT NULL, 
    description TEXT NOT NULL, 
    instructions TEXT NOT NULL, 
    category VARCHAR(50) NOT NULL, 
    difficulty VARCHAR(10) NOT NULL, 
    estimated_duration_minutes INTEGER NOT NULL, 
    xp_reward INTEGER NOT NULL, 
    repeatability VARCHAR(20) NOT NULL, 
    proof_requirement VARCHAR(40) NOT NULL, 
    reflection_prompt VARCHAR(240), 
    is_active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_quest_difficulty CHECK (difficulty IN ('easy', 'medium', 'hard')), 
    CONSTRAINT check_quest_values CHECK (estimated_duration_minutes >= 1 AND xp_reward >= 0), 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_quests_code ON quests (code);

CREATE INDEX ix_quests_category ON quests (category);

CREATE INDEX ix_quests_difficulty ON quests (difficulty);

CREATE TABLE mission_definitions (
    id UUID NOT NULL, 
    code VARCHAR(12) NOT NULL, 
    title VARCHAR(120) NOT NULL, 
    description TEXT NOT NULL, 
    mission_type VARCHAR(10) NOT NULL, 
    metric VARCHAR(30) NOT NULL, 
    target_value INTEGER NOT NULL, 
    category_filter JSON, 
    reward_xp INTEGER NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_mission_type CHECK (mission_type IN ('daily', 'weekly')), 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_mission_definitions_code ON mission_definitions (code);

CREATE INDEX ix_mission_definitions_mission_type ON mission_definitions (mission_type);

CREATE TABLE achievement_definitions (
    id UUID NOT NULL, 
    code VARCHAR(12) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    description TEXT NOT NULL, 
    metric VARCHAR(30) NOT NULL, 
    target_value INTEGER NOT NULL, 
    category_filter VARCHAR(50), 
    reward_xp INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (code)
);

CREATE UNIQUE INDEX ix_achievement_definitions_code ON achievement_definitions (code);

CREATE TABLE xp_transactions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    amount INTEGER NOT NULL, 
    transaction_type VARCHAR(40) NOT NULL, 
    source_type VARCHAR(30) NOT NULL, 
    source_id VARCHAR(100) NOT NULL, 
    lifetime_before INTEGER NOT NULL, 
    lifetime_after INTEGER NOT NULL, 
    idempotency_key VARCHAR(180) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_xp_amount CHECK (amount > 0), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_xp_transactions_user_id ON xp_transactions (user_id);

CREATE UNIQUE INDEX ix_xp_transactions_idempotency_key ON xp_transactions (idempotency_key);

CREATE INDEX idx_xp_transactions_user_date ON xp_transactions (user_id, created_at);

CREATE TABLE user_quest_instances (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    quest_id UUID NOT NULL, 
    activity_id UUID NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    abandoned_at TIMESTAMP WITH TIME ZONE, 
    reflection VARCHAR(1000), 
    xp_claimed BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_quest_instance_status CHECK (status IN ('active', 'completed', 'abandoned')), 
    FOREIGN KEY(activity_id) REFERENCES activities (id) ON DELETE CASCADE, 
    FOREIGN KEY(quest_id) REFERENCES quests (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (activity_id)
);

CREATE INDEX ix_user_quest_instances_user_id ON user_quest_instances (user_id);

CREATE INDEX ix_user_quest_instances_quest_id ON user_quest_instances (quest_id);

CREATE INDEX ix_user_quest_instances_status ON user_quest_instances (status);

CREATE TABLE quest_favorites (
    user_id UUID NOT NULL, 
    quest_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (user_id, quest_id), 
    FOREIGN KEY(quest_id) REFERENCES quests (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE user_missions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    mission_id UUID NOT NULL, 
    period_key VARCHAR(20) NOT NULL, 
    current_progress INTEGER NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    reward_claimed BOOLEAN NOT NULL, 
    start_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    end_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    claimed_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(mission_id) REFERENCES mission_definitions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_user_mission_period UNIQUE (user_id, mission_id, period_key)
);

CREATE INDEX ix_user_missions_user_id ON user_missions (user_id);

CREATE TABLE user_achievements (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    achievement_id UUID NOT NULL, 
    unlocked_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    claimed BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(achievement_id) REFERENCES achievement_definitions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_user_achievement UNIQUE (user_id, achievement_id)
);

CREATE INDEX ix_user_achievements_user_id ON user_achievements (user_id);

UPDATE alembic_version SET version_num='a1f4c2d9e710' WHERE alembic_version.version_num = 'db98869da4be';

-- Running upgrade a1f4c2d9e710 -> b7d210c42f01

ALTER TABLE public."achievement_definitions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."activities" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."activity_check_ins" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."activity_participants" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."consent_records" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."focus_sessions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."friend_requests" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."friendships" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."garden_catalog_items" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."garden_items" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."gardens" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."group_invites" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."group_members" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."groups" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."mission_definitions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."notifications" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."point_transactions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."proof_confirmations" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."proof_submissions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."quest_favorites" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."quests" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."screening_events" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."usage_summaries" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."user_achievements" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."user_missions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."user_preferences" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."user_progression" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."user_quest_instances" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."users" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."xp_transactions" ENABLE ROW LEVEL SECURITY;

ALTER TABLE public."alembic_version" ENABLE ROW LEVEL SECURITY;

UPDATE alembic_version SET version_num='b7d210c42f01' WHERE alembic_version.version_num = 'a1f4c2d9e710';

-- Running upgrade b7d210c42f01 -> c8e31a04d912

-- Shared by the Alembic migration and the Supabase SQL Editor script.
-- No accounts are deleted when this setup script is run.
ALTER TABLE public.point_transactions ALTER COLUMN user_id DROP NOT NULL;

-- Resolve actual constraint names, including databases created before Alembic.
DO $$
DECLARE link record;
BEGIN
  FOR link IN
    SELECT c.conname, c.conrelid::regclass AS table_name
    FROM pg_constraint c
    WHERE c.contype = 'f' AND (
      (c.conrelid = 'public.point_transactions'::regclass
       AND c.confrelid IN ('public.users'::regclass, 'public.activity_participants'::regclass))
      OR (c.conrelid = 'public.activity_participants'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.proof_submissions'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.proof_confirmations'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.group_invites'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.activities'::regclass AND c.confrelid = 'public.groups'::regclass)
    )
  LOOP
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', link.table_name, link.conname);
  END LOOP;
END $$;

ALTER TABLE public.point_transactions ADD CONSTRAINT fk_points_user_deletion
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;
ALTER TABLE public.point_transactions ADD CONSTRAINT fk_points_participant_deletion
  FOREIGN KEY (activity_participant_id) REFERENCES public.activity_participants(id) ON DELETE SET NULL;
ALTER TABLE public.activity_participants ADD CONSTRAINT fk_participant_user_deletion
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.proof_submissions ADD CONSTRAINT fk_proof_reviewer_deletion
  FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE SET NULL;
ALTER TABLE public.proof_confirmations ADD CONSTRAINT fk_confirmation_user_deletion
  FOREIGN KEY (confirmed_by) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.group_invites ADD CONSTRAINT fk_invite_creator_deletion
  FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.activities ADD CONSTRAINT fk_activity_group_deletion
  FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

CREATE OR REPLACE FUNCTION public.jomo_prepare_account_deletion()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  owned_group record;
  successor uuid;
BEGIN
  -- Lock affected groups in a stable order. Prefer an existing owner/admin,
  -- then the longest-standing active member. Departed/removed users never inherit.
  FOR owned_group IN
    SELECT g.id, g.created_by FROM public.groups g
    WHERE g.created_by = OLD.id OR EXISTS (
      SELECT 1 FROM public.group_members m
      WHERE m.group_id = g.id AND m.user_id = OLD.id
        AND m.role = 'owner' AND m.status = 'active'
    ) ORDER BY g.id FOR UPDATE
  LOOP
    successor := NULL;
    SELECT m.user_id INTO successor FROM public.group_members m
    WHERE m.group_id = owned_group.id AND m.user_id <> OLD.id AND m.status = 'active'
    ORDER BY CASE m.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END,
      m.joined_at, m.user_id LIMIT 1 FOR UPDATE;
    IF successor IS NULL THEN
      -- A group with no remaining active members has no one to retain its garden.
      DELETE FROM public.groups WHERE id = owned_group.id;
    ELSE
      UPDATE public.groups SET created_by = successor
        WHERE id = owned_group.id AND created_by = OLD.id;
      IF NOT EXISTS (
        SELECT 1 FROM public.group_members
        WHERE group_id = owned_group.id AND user_id <> OLD.id
          AND role = 'owner' AND status = 'active'
      ) THEN
        UPDATE public.group_members SET role = 'owner'
          WHERE group_id = owned_group.id AND user_id = successor;
      END IF;
    END IF;
  END LOOP;

  -- Shared activities remain usable; personal activities and their evidence go.
  UPDATE public.activities a SET created_by = g.created_by
    FROM public.groups g
    WHERE a.group_id = g.id AND a.created_by = OLD.id;
  DELETE FROM public.activities WHERE created_by = OLD.id;

  -- Retain group balances and accounting amounts without the deleted identity.
  -- Replace free text and idempotency keys that might identify the former user.
  UPDATE public.point_transactions
    SET user_id = NULL, activity_participant_id = NULL,
        reason = 'Former member transaction', idempotency_key = 'deleted-account:' || id::text
    WHERE user_id = OLD.id;
  -- Other users' notifications can contain this user's name/ID in free text.
  DELETE FROM public.notifications
    WHERE payload::text LIKE '%' || OLD.id::text || '%';
  RETURN OLD;
END $$;

REVOKE ALL ON FUNCTION public.jomo_prepare_account_deletion() FROM PUBLIC;
DROP TRIGGER IF EXISTS jomo_prepare_account_deletion ON public.users;
CREATE TRIGGER jomo_prepare_account_deletion BEFORE DELETE ON public.users
  FOR EACH ROW EXECUTE FUNCTION public.jomo_prepare_account_deletion();

CREATE OR REPLACE FUNCTION public.jomo_delete_app_account()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
  DELETE FROM public.users WHERE id = OLD.id;
  RETURN OLD;
END $$;
REVOKE ALL ON FUNCTION public.jomo_delete_app_account() FROM PUBLIC;

-- An ordinary PostgreSQL installation has no auth schema. Supabase does.
DO $$
BEGIN
  IF to_regclass('auth.users') IS NOT NULL THEN
    -- Enforce the identity link for new writes, including requests that began
    -- before deletion. NOT VALID tolerates old local/demo rows without deleting them.
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
      WHERE conrelid = 'public.users'::regclass AND conname = 'fk_jomo_user_auth') THEN
      EXECUTE 'ALTER TABLE public.users ADD CONSTRAINT fk_jomo_user_auth
        FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE NOT VALID';
    END IF;
    EXECUTE 'DROP TRIGGER IF EXISTS jomo_delete_app_account ON auth.users';
    EXECUTE 'CREATE TRIGGER jomo_delete_app_account BEFORE DELETE ON auth.users
      FOR EACH ROW EXECUTE FUNCTION public.jomo_delete_app_account()';
  END IF;
END $$;


UPDATE alembic_version SET version_num='c8e31a04d912' WHERE alembic_version.version_num = 'b7d210c42f01';

COMMIT;

