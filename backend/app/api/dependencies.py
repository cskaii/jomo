from typing import Annotated
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, verify_auth_token
from app.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[AuthenticatedUser, Depends(verify_auth_token)]
