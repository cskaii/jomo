export const ActivityStatus = {
  DRAFT: "draft",
  PUBLISHED: "published",
  ACTIVE: "active",
  AWAITING_PROOF: "awaiting_proof",
  UNDER_REVIEW: "under_review",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
  EXPIRED: "expired",
  REJECTED: "rejected",
} as const;
export type ActivityStatus = (typeof ActivityStatus)[keyof typeof ActivityStatus];

export const ParticipantStatus = {
  JOINED: "joined",
  ACTIVE: "active",
  LEFT: "left",
  AWAITING_PROOF: "awaiting_proof",
  COMPLETED: "completed",
  REJECTED: "rejected",
} as const;
export type ParticipantStatus = (typeof ParticipantStatus)[keyof typeof ParticipantStatus];

export const GardenType = {
  PERSONAL: "personal",
  GROUP: "group",
} as const;
export type GardenType = (typeof GardenType)[keyof typeof GardenType];

export const ProofType = {
  NONE: "none",
  PHOTO: "photo",
  GROUP_CONFIRMATION: "group_confirmation",
  PHOTO_OR_GROUP_CONFIRMATION: "photo_or_group_confirmation",
} as const;
export type ProofType = (typeof ProofType)[keyof typeof ProofType];

export const ProofStatus = {
  PENDING: "pending",
  ACCEPTED: "accepted",
  REJECTED: "rejected",
} as const;
export type ProofStatus = (typeof ProofStatus)[keyof typeof ProofStatus];

export const FocusStatus = {
  ACTIVE: "active",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
} as const;
export type FocusStatus = (typeof FocusStatus)[keyof typeof FocusStatus];

export const UsageSource = {
  NATIVE: "native",
  MANUAL: "manual",
  IMPORT: "import",
  DEMO: "demo",
} as const;
export type UsageSource = (typeof UsageSource)[keyof typeof UsageSource];

export const GroupRole = {
  OWNER: "owner",
  ADMIN: "admin",
  MEMBER: "member",
} as const;
export type GroupRole = (typeof GroupRole)[keyof typeof GroupRole];

export const GroupMemberStatus = {
  ACTIVE: "active",
  LEFT: "left",
  REMOVED: "removed",
} as const;
export type GroupMemberStatus = (typeof GroupMemberStatus)[keyof typeof GroupMemberStatus];

export const FriendRequestStatus = {
  PENDING: "pending",
  ACCEPTED: "accepted",
  DECLINED: "declined",
  CANCELLED: "cancelled",
} as const;
export type FriendRequestStatus = (typeof FriendRequestStatus)[keyof typeof FriendRequestStatus];

export const GroupVisibility = {
  PRIVATE: "private",
  INVITE_ONLY: "invite_only",
} as const;
export type GroupVisibility = (typeof GroupVisibility)[keyof typeof GroupVisibility];

export const ActivityVisibility = {
  PERSONAL: "personal",
  GROUP: "group",
} as const;
export type ActivityVisibility = (typeof ActivityVisibility)[keyof typeof ActivityVisibility];

export const GardenItemType = {
  SEED: "seed",
  PLANT: "plant",
  PET: "pet",
  DECORATION: "decoration",
} as const;
export type GardenItemType = (typeof GardenItemType)[keyof typeof GardenItemType];

export const PointTransactionType = {
  EARN: "earn",
  SPEND: "spend",
  REFUND: "refund",
  ADJUSTMENT: "adjustment",
} as const;
export type PointTransactionType = (typeof PointTransactionType)[keyof typeof PointTransactionType];

export const LocationPrecision = {
  APPROXIMATE: "approximate",
  PRECISE: "precise",
} as const;
export type LocationPrecision = (typeof LocationPrecision)[keyof typeof LocationPrecision];

export const ScreeningType = {
  PII: "pii",
  HARMFUL_CONTENT: "harmful_content",
  IMAGE: "image",
} as const;
export type ScreeningType = (typeof ScreeningType)[keyof typeof ScreeningType];

export const ScreeningResultStatus = {
  COMPLETED: "completed",
  PARTIAL: "partial",
  ERROR: "error",
} as const;
export type ScreeningResultStatus = (typeof ScreeningResultStatus)[keyof typeof ScreeningResultStatus];
