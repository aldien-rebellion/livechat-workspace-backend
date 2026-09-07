from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    stmt = select(User).where(User.username == user_in.username)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The username is already registered.",
        )

    # Hash the password
    hashed_password = get_password_hash(user_in.password)

    # Determine role (for demo purposes, first user or 'admin' gets admin role, others viewer)
    role = "admin" if "admin" in user_in.username.lower() else "viewer"

    # Create new user
    new_user = User(username=user_in.username, password_hash=hashed_password, role=role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Find user by username
    stmt = select(User).where(User.username == user_in.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    # Compare password hashes
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Sign JWT token with userId and role in payload
    access_token = create_access_token(subject=user.id, role=user.role)

    return {"access_token": access_token, "token_type": "bearer"}
