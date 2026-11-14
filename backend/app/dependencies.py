from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession) -> User:
    user = db.scalar(
        select(User).where(User.email == settings.dev_user_email)
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="开发用户尚未初始化，请先执行种子脚本",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

