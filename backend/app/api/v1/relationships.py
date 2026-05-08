import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.relationship import RelationshipProfile, InteractionRecord
from app.schemas.relationship import (
    RelationshipCreate, RelationshipUpdate, RelationshipOut,
    RelationshipDetail, InteractionOut, CommunicationStrategy,
)
from app.services.relationship_service import (
    create_relationship, update_relationship, format_relationship_out, generate_strategy,
)

router = APIRouter(prefix="/relationships", tags=["关系档案"])


@router.post("", response_model=RelationshipOut)
async def create(
    data: RelationshipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await create_relationship(db, current_user.id, data.model_dump())
    return format_relationship_out(profile)


@router.get("", response_model=list[RelationshipOut])
async def list_relationships(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RelationshipProfile)
        .where(RelationshipProfile.user_id == current_user.id)
        .order_by(RelationshipProfile.last_interaction_at.desc().nulls_last())
    )
    profiles = result.scalars().all()
    return [format_relationship_out(p) for p in profiles]


@router.get("/{profile_id}", response_model=RelationshipDetail)
async def get_relationship(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RelationshipProfile)
        .where(RelationshipProfile.id == profile_id, RelationshipProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="关系档案不存在")

    interactions_result = await db.execute(
        select(InteractionRecord)
        .where(InteractionRecord.relationship_id == profile_id)
        .order_by(InteractionRecord.created_at.desc()).limit(20)
    )
    interactions = interactions_result.scalars().all()

    interaction_out = []
    for i in interactions:
        tags = json.loads(i.tags) if i.tags else None
        interaction_out.append(InteractionOut(
            id=i.id, summary=i.summary, outcome=i.outcome,
            tags=tags, created_at=i.created_at,
        ))

    return RelationshipDetail(
        **format_relationship_out(profile),
        recent_interactions=interaction_out,
    )


@router.put("/{profile_id}", response_model=RelationshipOut)
async def update(
    profile_id: int,
    data: RelationshipUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RelationshipProfile)
        .where(RelationshipProfile.id == profile_id, RelationshipProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="关系档案不存在")

    profile = await update_relationship(db, profile, data.model_dump(exclude_unset=True))
    return format_relationship_out(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RelationshipProfile)
        .where(RelationshipProfile.id == profile_id, RelationshipProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="关系档案不存在")
    await db.delete(profile)
    await db.commit()


@router.get("/{profile_id}/strategy", response_model=CommunicationStrategy)
async def get_strategy(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RelationshipProfile)
        .where(RelationshipProfile.id == profile_id, RelationshipProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="关系档案不存在")

    strategy = await generate_strategy(db, profile)
    return CommunicationStrategy(**strategy)