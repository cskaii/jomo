from enum import Enum


class ActivityStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    AWAITING_PROOF = "awaiting_proof"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class ParticipantStatus(str, Enum):
    JOINED = "joined"
    ACTIVE = "active"
    LEFT = "left"
    AWAITING_PROOF = "awaiting_proof"
    COMPLETED = "completed"
    REJECTED = "rejected"


class GardenType(str, Enum):
    PERSONAL = "personal"
    GROUP = "group"


class ProofType(str, Enum):
    NONE = "none"
    PHOTO = "photo"
    GROUP_CONFIRMATION = "group_confirmation"
    PHOTO_OR_GROUP_CONFIRMATION = "photo_or_group_confirmation"


class ProofStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FocusStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UsageSource(str, Enum):
    NATIVE = "native"
    MANUAL = "manual"
    IMPORT = "import"
    DEMO = "demo"


class GroupRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class GroupMemberStatus(str, Enum):
    ACTIVE = "active"
    LEFT = "left"
    REMOVED = "removed"


class FriendRequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class GroupVisibility(str, Enum):
    PRIVATE = "private"
    INVITE_ONLY = "invite_only"


class ActivityVisibility(str, Enum):
    PERSONAL = "personal"
    GROUP = "group"


class GardenItemType(str, Enum):
    SEED = "seed"
    PLANT = "plant"
    PET = "pet"
    DECORATION = "decoration"


class PointTransactionType(str, Enum):
    EARN = "earn"
    SPEND = "spend"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class LocationPrecision(str, Enum):
    APPROXIMATE = "approximate"
    PRECISE = "precise"


class ScreeningType(str, Enum):
    PII = "pii"
    HARMFUL_CONTENT = "harmful_content"
    IMAGE = "image"


class ScreeningResultStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
