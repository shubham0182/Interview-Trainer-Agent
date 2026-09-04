"""
Profile service — candidate profile CRUD.

Each user has exactly one CandidateProfile (unique FK).
This service provides get-or-create semantics so callers never need
to handle the "profile not yet created" case themselves.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_profile import CandidateProfile
from app.schemas.profile import ProfileUpdateRequest


async def get_or_create_profile(
    db: AsyncSession, user_id: uuid.UUID
) -> CandidateProfile:
    """
    Return the existing CandidateProfile for `user_id`, or create a blank one.

    Uses flush + refresh so server-side defaults (updated_at) are populated
    before the caller serializes the returned object.
    """
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CandidateProfile(
            id=uuid.uuid4(),
            user_id=user_id,
            skills=[],
            education=[],
            experience=[],
            projects=[],
        )
        db.add(profile)
        await db.flush()
        await db.refresh(profile)

    return profile


async def update_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: ProfileUpdateRequest,
) -> CandidateProfile:
    """
    Upsert the candidate profile for `user_id`.

    Only fields explicitly set in the request are updated (None = not provided).
    Uses Pydantic `model_dump(exclude_unset=True)` for partial-update semantics.
    """
    profile = await get_or_create_profile(db, user_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            # JSONB fields (education/experience/projects) are lists of Pydantic models
            # — convert them to plain dicts for storage
            if isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                value = [item.model_dump() for item in value]
            setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)
    return profile
