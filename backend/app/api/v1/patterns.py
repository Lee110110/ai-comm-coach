import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.pattern import CommunicationPattern, PatternInsight
from app.schemas.pattern import PatternCurrent, InsightOut, PatternTrend
from app.services.pattern_service import get_or_create_pattern, compute_pattern, get_pattern_trend

router = APIRouter(prefix="/patterns", tags=["沟通画像"])


@router.get("/current", response_model=PatternCurrent)
async def get_current_pattern(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = await get_or_create_pattern(db, current_user.id)
    return PatternCurrent(
        dimensions={
            "assertiveness": pattern.assertiveness,
            "empathy": pattern.empathy,
            "clarity": pattern.clarity,
            "adaptability": pattern.adaptability,
            "conflict_handling": pattern.conflict_handling,
            "active_listening": pattern.active_listening,
        },
        data_source_count=pattern.data_source_count,
        last_computed_at=pattern.last_computed_at,
    )


@router.get("/insights", response_model=list[InsightOut])
async def get_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = await get_or_create_pattern(db, current_user.id)
    result = await db.execute(
        select(PatternInsight)
        .where(PatternInsight.pattern_id == pattern.id)
        .order_by(PatternInsight.created_at.desc())
    )
    insights = result.scalars().all()

    out = []
    for i in insights:
        evidence = json.loads(i.evidence) if i.evidence else None
        out.append(InsightOut(
            id=i.id, insight_type=i.insight_type, category=i.category,
            title=i.title, description=i.description, evidence=evidence,
            suggested_practice=i.suggested_practice, is_read=i.is_read,
        ))
    return out


@router.post("/recompute", response_model=PatternCurrent)
async def recompute_pattern(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = await compute_pattern(db, current_user.id)
    return PatternCurrent(
        dimensions={
            "assertiveness": pattern.assertiveness,
            "empathy": pattern.empathy,
            "clarity": pattern.clarity,
            "adaptability": pattern.adaptability,
            "conflict_handling": pattern.conflict_handling,
            "active_listening": pattern.active_listening,
        },
        data_source_count=pattern.data_source_count,
        last_computed_at=pattern.last_computed_at,
    )


@router.get("/trend", response_model=PatternTrend)
async def get_trend(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_pattern_trend(db, current_user.id)


@router.put("/insights/{insight_id}/read")
async def mark_insight_read(
    insight_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PatternInsight)
        .where(PatternInsight.id == insight_id, PatternInsight.user_id == current_user.id)
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="洞察不存在")
    insight.is_read = True
    await db.commit()
    return {"status": "ok"}