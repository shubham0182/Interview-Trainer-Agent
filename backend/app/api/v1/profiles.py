"""
Profile API routes.

Endpoints:
  GET /api/v1/profiles/me  — get or create the authenticated user's profile
  PUT /api/v1/profiles/me  — update the authenticated user's profile

Route handlers are thin: auth → call service → return schema.
Resume upload endpoint is implemented in ST-05.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.profile_service import get_or_create_profile, update_profile

router = APIRouter()


@router.get(
    "/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the authenticated user's candidate profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """
    Return the authenticated user's candidate profile.
    Creates a blank profile if one does not yet exist.
    """
    profile = await get_or_create_profile(db, current_user.id)
    return ProfileResponse.model_validate(profile)


@router.put(
    "/me",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the authenticated user's candidate profile",
)
async def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """
    Partially update the authenticated user's candidate profile.
    Only provided fields are updated; omitted fields are left unchanged.
    """
    profile = await update_profile(db, current_user.id, payload)
    return ProfileResponse.model_validate(profile)
