from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister


def register_user(db: Session, user: UserRegister):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        return None

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def login_user(db: Session, user: UserLogin):
    db_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if not db_user:
        return None

    if not verify_password(
        user.password,
        db_user.password_hash,
    ):
        return None

    access_token = create_access_token(
        data={
            "sub": str(db_user.id)
        }
    )

    return access_token