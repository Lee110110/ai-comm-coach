import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import MessagePolish
from app.models.relationship import RelationshipProfile
from sqlalchemy import select

from app.services.llm_service import llm_service
from app.services.prompt_templates import MESSAGE_POLISH_SYSTEM, MESSAGE_POLISH_USER

logger = logging.getLogger(__name__)


async def polish_message(
    db: AsyncSession,
    user_id: int,
    data: dict,
) -> MessagePolish:
    relationship_info = "未指定"
    if data.get("relationship_id"):
        result = await db.execute(
            select(RelationshipProfile).where(RelationshipProfile.id == data["relationship_id"])
        )
        rel = result.scalar_one_or_none()
        if rel:
            relationship_info = f"姓名：{rel.name}，关系：{rel.relation_type}，偏好：{rel.preferences or '无'}"

    prompt = MESSAGE_POLISH_USER.format(
        original_message=data["original_message"],
        context=data.get("context") or "无特殊上下文",
        tone=data.get("tone") or "自然得体",
        relationship_info=relationship_info,
    )

    result, input_tokens, output_tokens = await llm_service.call_json(
        messages=[
            {"role": "system", "content": MESSAGE_POLISH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )

    message = MessagePolish(
        user_id=user_id,
        relationship_id=data.get("relationship_id"),
        original_message=data["original_message"],
        context=data.get("context"),
        tone=data.get("tone"),
        polished_message=result.get("polished_message"),
        changes=json.dumps(result.get("changes"), ensure_ascii=False),
        alternative_versions=json.dumps(result.get("alternative_versions"), ensure_ascii=False),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


def format_message_out(msg: MessagePolish) -> dict:
    changes = json.loads(msg.changes) if msg.changes else None
    alternatives = json.loads(msg.alternative_versions) if msg.alternative_versions else None

    return {
        "id": msg.id,
        "original_message": msg.original_message,
        "polished_message": msg.polished_message,
        "changes": changes,
        "alternative_versions": alternatives,
        "tone": msg.tone,
        "created_at": msg.created_at,
    }