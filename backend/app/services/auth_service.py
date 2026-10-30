"""
TruthLens - Authentication Service & Dependency Injection
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.security import decode_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves user by case-insensitive email address."""
    return db.query(User).filter(User.email == email.lower().strip()).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Creates a new registered user with bcrypt-hashed credentials."""
    existing = get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    db_user = User(
        email=user_in.email.lower().strip(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Validates user login credentials."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    FastAPI dependency: Enforces authenticated user via Bearer JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    FastAPI dependency: Resolves current user if token present, otherwise None.
    Allows demo/public analysis while binding to user when logged in.
    """
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    email: str = payload.get("sub")
    if not email:
        return None
    return get_user_by_email(db, email=email)

