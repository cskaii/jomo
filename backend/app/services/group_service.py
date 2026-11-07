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
from app.services.notification_service import notify, resolve_notices
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
        self.require_manager(user_id, group_id)
        if data.receiver_id and not self.db.get(User, data.receiver_id):
            raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "Profile not found."})
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=data.expires_in_hours)

        invite = GroupInvite(
            group_id=group_id,
            created_by=user_id,
            token_hash=token_hash,
            receiver_id=data.receiver_id,
            expires_at=expires_at,
            max_uses=data.max_uses,
            uses_count=0,
        )
        self.db.add(invite)
        self.db.flush()
        if data.receiver_id:
            notify(self.db, data.receiver_id, "group_invite", "Group invitation", "You have been invited to a private group.", "/friends", invite_id=invite.id, group_id=group_id)
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
        self._accept(user_id, invite)

    def _accept(self, user_id, invite):
        from app.utils.user_time import utc
        if not invite or invite.revoked_at or utc(invite.expires_at) <= datetime.now(timezone.utc):
            raise HTTPException(400, detail={"code": "INVALID_INVITE", "message": "Invitation is invalid, expired or revoked."})
        group = self.db.query(Group).filter_by(id=invite.group_id).populate_existing().with_for_update().first()
        if not group or group.archived_at or (invite.receiver_id and invite.receiver_id != user_id):
            raise HTTPException(403, detail={"code": "INVITE_DENIED", "message": "This invitation is not available to you."})
        self.db.refresh(invite)
        if invite.revoked_at or (invite.max_uses and invite.uses_count >= invite.max_uses):
            raise HTTPException(400, detail={"code": "INVITE_EXHAUSTED", "message": "Invitation is revoked or fully used."})
        existing = self.db.get(GroupMember, (invite.group_id, user_id))
        if existing and existing.status == "active":
            return
        if existing and existing.status == "removed":
            raise HTTPException(403, detail={"code": "MEMBERSHIP_REMOVED", "message": "A removed member cannot rejoin using an invitation."})
        if existing:
            existing.status, existing.role, existing.left_at = "active", "member", None
        else:
            self.db.add(GroupMember(group_id=invite.group_id, user_id=user_id, role="member", status="active"))
        invite.uses_count += 1
        resolve_notices(self.db, user_id, "invite_id", invite.id)
        notify(self.db, group.created_by, "group_joined", "A member joined", "A new member joined your group.", f"/friends/groups/{group.id}", group_id=group.id)
        self.db.commit()

    def require_manager(self, user_id, group_id, owner_only=False):
        group = self.db.query(Group).filter_by(id=group_id).populate_existing().with_for_update().first()
        member = self.check_membership(user_id, group_id)
        if not group or group.archived_at or member.role not in (("owner",) if owner_only else ("owner", "admin")):
            raise HTTPException(403, detail={"code": "GROUP_MANAGEMENT_DENIED", "message": "You do not have permission to manage this group."})
        return group

    def manage_member(self, actor, group_id, user_id, role=None):
        self.require_manager(actor, group_id, owner_only=True)
        member = self.check_membership(user_id, group_id)
        if user_id == actor or member.role == "owner":
            raise HTTPException(400, detail={"code": "OWNER_PROTECTED", "message": "Transfer ownership before changing the owner."})
        if role:
            member.role = role
        else:
            member.status, member.left_at = "removed", datetime.now(timezone.utc)
        notify(self.db, user_id, "membership_changed", "Group membership updated", "Your group role or access has changed.", "/friends", group_id=group_id)
        self.db.commit()

    def transfer(self, actor, group_id, user_id):
        group = self.require_manager(actor, group_id, owner_only=True)
        successor = self.check_membership(user_id, group_id)
        if user_id == actor:
            raise HTTPException(400, detail={"code": "SAME_OWNER", "message": "Choose another active member."})
        self.check_membership(actor, group_id).role = "admin"
        successor.role, group.created_by = "owner", user_id
        notify(self.db, user_id, "ownership", "Group ownership transferred", "You now manage this group.", f"/friends/groups/{group_id}", group_id=group_id)
        self.db.commit()

    def list_invites(self, actor, group_id):
        self.require_manager(actor, group_id)
        return [{"id": item.id, "receiver_id": item.receiver_id, "expires_at": item.expires_at,
                 "uses_count": item.uses_count, "max_uses": item.max_uses, "revoked_at": item.revoked_at}
                for item in self.db.query(GroupInvite).filter_by(group_id=group_id).order_by(GroupInvite.created_at.desc()).limit(50)]

    def revoke(self, actor, group_id, invite_id):
        self.require_manager(actor, group_id)
        invite = self.db.query(GroupInvite).filter_by(id=invite_id, group_id=group_id).first()
        if not invite:
            raise HTTPException(404, detail={"code": "INVITE_NOT_FOUND", "message": "Invitation not found."})
        invite.revoked_at = datetime.now(timezone.utc)
        self.db.commit()

    def accept_targeted(self, actor, invite_id):
        invite = self.db.query(GroupInvite).filter_by(id=invite_id, receiver_id=actor).first()
        self._accept(actor, invite)

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
            group = self.db.get(Group, group_id)
            group.archived_at = datetime.now(timezone.utc)
            self.db.query(GroupInvite).filter_by(group_id=group_id).update({"revoked_at": datetime.now(timezone.utc)}, synchronize_session=False)

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
