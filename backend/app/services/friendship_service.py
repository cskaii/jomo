import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.friendship import Friendship, FriendRequest
from app.schemas.group import FriendResponse


class FriendshipService:
    def __init__(self, db: Session):
        self.db = db

    def list_friends(self, user_id: uuid.UUID) -> List[FriendResponse]:
        friendships = (
            self.db.query(Friendship)
            .filter(or_(Friendship.user_low_id == user_id, Friendship.user_high_id == user_id))
            .all()
        )
        friend_ids = [
            f.user_high_id if f.user_low_id == user_id else f.user_low_id for f in friendships
        ]
        if not friend_ids:
            return []

        users = self.db.query(User).filter(User.id.in_(friend_ids)).all()
        return [
            FriendResponse(
                id=u.id,
                username=u.username,
                display_name=u.display_name,
                avatar_url=u.avatar_url,
            )
            for u in users
        ]

    def send_request(self, sender_id: uuid.UUID, receiver_id: uuid.UUID) -> FriendRequest:
        if sender_id == receiver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "SELF_FRIEND_REQUEST", "message": "Cannot send friend request to yourself."},
            )

        # Check existing pending request
        existing = (
            self.db.query(FriendRequest)
            .filter(
                or_(
                    and_(FriendRequest.sender_id == sender_id, FriendRequest.receiver_id == receiver_id),
                    and_(FriendRequest.sender_id == receiver_id, FriendRequest.receiver_id == sender_id),
                ),
                FriendRequest.status == "pending",
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DUPLICATE_REQUEST", "message": "A pending request already exists between these users."},
            )

        req = FriendRequest(sender_id=sender_id, receiver_id=receiver_id, status="pending")
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def accept_request(self, request_id: uuid.UUID, receiver_id: uuid.UUID) -> None:
        req = self.db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
        if not req or req.receiver_id != receiver_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Friend request not found or not authorised."},
            )

        if req.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE", "message": "Request is no longer pending."},
            )

        req.status = "accepted"
        req.responded_at = datetime.now(timezone.utc)

        # Canonical ordering for friendship low < high
        low_id, high_id = sorted([req.sender_id, req.receiver_id])
        friendship = Friendship(user_low_id=low_id, user_high_id=high_id)
        self.db.add(friendship)
        self.db.commit()

    def decline_request(self, request_id: uuid.UUID, receiver_id: uuid.UUID) -> None:
        req = self.db.query(FriendRequest).filter(FriendRequest.id == request_id).first()
        if not req or req.receiver_id != receiver_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Friend request not found or not authorised."},
            )
        req.status = "declined"
        req.responded_at = datetime.now(timezone.utc)
        self.db.commit()
