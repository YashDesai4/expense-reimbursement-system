from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import Role, User

bearer = HTTPBearer()


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), database: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(credentials.credentials)
        user = database.get(User, int(payload["sub"]))
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from error
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def manager_only(user: User = Depends(current_user)) -> User:
    if user.role != Role.manager:
        raise HTTPException(status_code=403, detail="Manager role required")
    return user
