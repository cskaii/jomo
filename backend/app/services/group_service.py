import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.group import Group, GroupMember, GroupInvite
from app.models.user import User
from app.models.garden import Garden
from app.schemas.group import GroupCreateRequest, GroupUpdateRequest, GroupInviteCreateRequest, GroupInviteResponse, GroupMemberResponse


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def check_membership(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupMember:
        member = (
            self.db.query(GroupMember)
            .filter(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.status == "active",
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "GROUP_MEMBERSHIP_REQUIRED", "message": "You must be a member of this group to perform this action."},
            )
        return member

    def list_groups(self, user_id: uuid.UUID) -> List[Group]:
        memberships = (
            self.db.query(GroupMember)
            .filter(GroupMember.user_id == user_id, GroupMember.status == "active")
            .all()
        )
        group_ids = [m.group_id for m in memberships]
        if not group_ids:
            return []
        return self.db.query(Group).filter(Group.id.in_(group_ids), Group.archived_at.is_(None)).all()

    def create_group(self, user_id: uuid.UUID, data: GroupCreateRequest) -> Group:
        group = Group(
            name=data.name,
            description=data.description,
            created_by=user_id,
            visibility=data.visibility.value,
        )
        self.db.add(group)
        self.db.flush()

        # Add creator as owner
        member = GroupMember(
            group_id=group.id,
            user_id=user_id,
            role="owner",
            status="active",
        )
        self.db.add(member)

        # Create group shared garden (Section 6.4: "Ensure group garden exists.")
        group_garden = Garden(
            garden_type="group",
            owner_user_id=None,
            owner_group_id=group.id,
            name=f"{group.name}'s Oasis",
            points_balance=0,
            growth_level=1,
        )
        self.db.add(group_garden)

        self.db.commit()
        self.db.refresh(group)
        return group

    def get_group_details(self, user_id: uuid.UUID, group_id: uuid.UUID) -> Group:
        self.check_membership(user_id, group_id)
        group = self.db.query(Group).filter(Group.id == group_id, Group.archived_at.is_(None)).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "GROUP_NOT_FOUND", "message": "Group not found."},
            )
        return group

    def update_group(self, user_id: uuid.UUID, group_id: uuid.UUID, data: GroupUpdateRequest) -> Group:
        member = self.check_membership(user_id, group_id)
        if member.role not in ("owner", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Only group owners or admins can update group settings."},
            )
        group = self.get_group_details(user_id, group_id)
        if data.name is not None:
            group.name = data.name
        if data.description is not None:
            group.description = data.description
        if data.visibility is not None:
            group.visibility = data.visibility.value
        group.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(group)
        return group

    def create_invite(self, user_id: uuid.UUID, group_id: uuid.UUID, data: GroupInviteCreateRequest) -> GroupInviteResponse:
        self.check_membership(user_id, group_id)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=data.expires_in_hours)

        invite = GroupInvite(
            group_id=group_id,
            created_by=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            max_uses=data.max_uses,
            uses_count=0,
        )
        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)

        return GroupInviteResponse(
            id=invite.id,
            group_id=invite.group_id,
            created_by=invite.created_by,
            invite_token=raw_token,
            expires_at=invite.expires_at,
            max_uses=invite.max_uses,
            uses_count=invite.uses_count,
            created_at=invite.created_at,
        )

    def accept_invite(self, user_id: uuid.UUID, raw_token: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        invite = (
            self.db.query(GroupInvite)
            .filter(
                GroupInvite.token_hash == token_hash,
                GroupInvite.revoked_at.is_(None),
                GroupInvite.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_INVITE", "message": "Invite token is invalid, expired, or revoked."},
            )

        if invite.max_uses and invite.uses_count >= invite.max_uses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVITE_EXHAUSTED", "message": "Invite token has reached maximum usage limit."},
            )

        # Check existing member
        existing = (
            self.db.query(GroupMember)
            .filter(GroupMember.group_id == invite.group_id, GroupMember.user_id == user_id)
            .first()
        )
        if existing:
            if existing.status == "active":
                return
            existing.status = "active"
            existing.left_at = None
        else:
            member = GroupMember(
                group_id=invite.group_id,
                user_id=user_id,
                role="member",
                status="active",
            )
            self.db.add(member)

        invite.uses_count += 1
        self.db.commit()

    def leave_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        member = self.check_membership(user_id, group_id)
        if member.role == "owner":
            # Check if there are other members to transfer or prevent leaving
            other_members = (
                self.db.query(GroupMember)
                .filter(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id != user_id,
                    GroupMember.status == "active",
                )
                .count()
            )
            if other_members > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "OWNER_CANNOT_LEAVE", "message": "Group owner must transfer ownership before leaving."},
                )

        member.status = "left"
        member.left_at = datetime.now(timezone.utc)
        self.db.commit()

    def list_members(self, user_id: uuid.UUID, group_id: uuid.UUID) -> List[GroupMemberResponse]:
        self.check_membership(user_id, group_id)
        members = (
            self.db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.status == "active")
            .all()
        )
        user_ids = [m.user_id for m in members]
        users = {u.id: u for u in self.db.query(User).filter(User.id.in_(user_ids)).all()}

        result = []
        for m in members:
            u = users.get(m.user_id)
            result.append(
                GroupMemberResponse(
                    group_id=m.group_id,
                    user_id=m.user_id,
                    username=u.username if u else None,
                    display_name=u.display_name if u else None,
                    role=m.role,
                    status=m.status,
                    joined_at=m.joined_at,
                )
            )
        return result
