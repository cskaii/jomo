from uuid import UUID
from fastapi import HTTPException, status


class PermissionDeniedError(HTTPException):
    def __init__(self, code: str, message: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": code, "message": message, "details": None},
        )


def check_is_self(actor_id: UUID, target_user_id: UUID) -> None:
    if actor_id != target_user_id:
        raise PermissionDeniedError(
            code="USER_MISMATCH",
            message="You do not have permission to perform this action for another user.",
        )
