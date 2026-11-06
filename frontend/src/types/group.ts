import { GroupRole, GroupMemberStatus, GroupVisibility } from "@/types/enums";

export interface Group {
  id: string;
  name: string;
  description?: string | null;
  created_by: string;
  visibility: GroupVisibility;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface GroupMember {
  group_id: string;
  user_id: string;
  username?: string | null;
  display_name?: string | null;
  role: GroupRole;
  status: GroupMemberStatus;
  joined_at: string;
}

export interface Friend {
  id: string;
  username: string;
  display_name: string;
  avatar_url?: string | null;
}
