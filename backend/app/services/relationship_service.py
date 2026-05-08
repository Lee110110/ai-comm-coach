import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.relationship import RelationshipProfile, InteractionRecord
from app.services.llm_service import llm_service
from app.services.prompt_templates import RELATIONSHIP_STRATEGY_SYSTEM, RELATIONSHIP_STRATEGY_USER

logger = logging.getLogger(__name__)


async def create_relationship(db: AsyncSession, user_id: int, data: dict) -> RelationshipProfile:
    profile = RelationshipProfile(
        user_id=user_id,
        name=data["name"],
        relation_type=data["relation_type"],
        avatar_emoji=data.get("avatar_emoji"),
        communication_style=json.dumps(data.get("communication_style", []), ensure_ascii=False),
        preferences=json.dumps(data.get("preferences", []), ensure_ascii=False),
        avoid_topics=json.dumps(data.get("avoid_topics", []), ensure_ascii=False),
        notes=data.get("notes"),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_relationship(db: AsyncSession, profile: RelationshipProfile, data: dict) -> RelationshipProfile:
    for key, value in data.items():
        if value is not None:
            if key in ("communication_style", "preferences", "avoid_topics"):
                setattr(profile, key, json.dumps(value, ensure_ascii=False))
            else:
                setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


def format_relationship_out(profile: RelationshipProfile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "relation_type": profile.relation_type,
        "avatar_emoji": profile.avatar_emoji,
        "communication_style": json.loads(profile.communication_style) if profile.communication_style else [],
        "preferences": json.loads(profile.preferences) if profile.preferences else [],
        "avoid_topics": json.loads(profile.avoid_topics) if profile.avoid_topics else [],
        "notes": profile.notes,
        "last_interaction_at": profile.last_interaction_at,
        "created_at": profile.created_at,
    }


async def generate_strategy(db: AsyncSession, profile: RelationshipProfile) -> dict:
    interactions = (await db.execute(
        select(InteractionRecord)
        .where(InteractionRecord.relationship_id == profile.id)
        .order_by(InteractionRecord.created_at.desc()).limit(10)
    )).scalars().all()

    recent_interactions = "\n".join(
        f"- {i.summary}（结果：{i.outcome or '未知'}）" for i in interactions
    ) if interactions else "暂无互动记录"

    prompt = RELATIONSHIP_STRATEGY_USER.format(
        name=profile.name,
        relation_type=profile.relation_type,
        communication_style=profile.communication_style or "未知",
        preferences=profile.preferences or "未知",
        avoid_topics=profile.avoid_topics or "无",
        notes=profile.notes or "无",
        recent_interactions=recent_interactions,
    )

    result, _, _ = await llm_service.call_json(
        messages=[
            {"role": "system", "content": RELATIONSHIP_STRATEGY_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )

    return result.get("communication_strategy", {})
