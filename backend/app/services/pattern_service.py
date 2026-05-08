import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pattern import CommunicationPattern, PatternInsight
from app.models.scenario import Scenario
from app.models.simulation import SimulationSession
from app.models.message import MessagePolish

from app.services.llm_service import llm_service
from app.services.prompt_templates import PATTERN_ANALYSIS_SYSTEM, PATTERN_ANALYSIS_USER

logger = logging.getLogger(__name__)


async def get_or_create_pattern(db: AsyncSession, user_id: int) -> CommunicationPattern:
    result = await db.execute(
        select(CommunicationPattern).where(CommunicationPattern.user_id == user_id)
    )
    pattern = result.scalar_one_or_none()
    if not pattern:
        pattern = CommunicationPattern(user_id=user_id)
        db.add(pattern)
        await db.commit()
        await db.refresh(pattern)
    return pattern


async def compute_pattern(db: AsyncSession, user_id: int) -> CommunicationPattern:
    pattern = await get_or_create_pattern(db, user_id)

    scenarios = (await db.execute(
        select(Scenario).where(Scenario.user_id == user_id).order_by(Scenario.created_at.desc()).limit(20)
    )).scalars().all()

    simulations = (await db.execute(
        select(SimulationSession).where(SimulationSession.user_id == user_id, SimulationSession.status == "completed")
        .order_by(SimulationSession.created_at.desc()).limit(10)
    )).scalars().all()

    messages = (await db.execute(
        select(MessagePolish).where(MessagePolish.user_id == user_id).order_by(MessagePolish.created_at.desc()).limit(20)
    )).scalars().all()

    interaction_data = []
    for s in scenarios:
        interaction_data.append(f"[急救话术] {s.title}: {s.description[:100]}")
    for sim in simulations:
        score = f"（得分{sim.overall_score}）" if sim.overall_score else ""
        interaction_data.append(f"[模拟演练] {sim.scenario_description[:100]}{score}")
    for m in messages:
        interaction_data.append(f"[消息润色] 原文：{m.original_message[:80]} → 润色：{(m.polished_message or '')[:80]}")

    current_pattern = {
        "assertiveness": pattern.assertiveness,
        "empathy": pattern.empathy,
        "clarity": pattern.clarity,
        "adaptability": pattern.adaptability,
        "conflict_handling": pattern.conflict_handling,
        "active_listening": pattern.active_listening,
        "data_source_count": pattern.data_source_count,
    }

    prompt = PATTERN_ANALYSIS_USER.format(
        interaction_data="\n".join(interaction_data) if interaction_data else "暂无互动数据",
        current_pattern=json.dumps(current_pattern, ensure_ascii=False),
    )

    result, input_tokens, output_tokens = await llm_service.call_json(
        messages=[
            {"role": "system", "content": PATTERN_ANALYSIS_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    dims = result.get("dimensions", {})
    pattern.assertiveness = dims.get("assertiveness", pattern.assertiveness)
    pattern.empathy = dims.get("empathy", pattern.empathy)
    pattern.clarity = dims.get("clarity", pattern.clarity)
    pattern.adaptability = dims.get("adaptability", pattern.adaptability)
    pattern.conflict_handling = dims.get("conflict_handling", pattern.conflict_handling)
    pattern.active_listening = dims.get("active_listening", pattern.active_listening)
    pattern.data_source_count = len(scenarios) + len(simulations) + len(messages)
    pattern.last_computed_at = datetime.now(timezone.utc)

    await db.execute(
        select(PatternInsight).where(PatternInsight.pattern_id == pattern.id)
    )
    old_insights = (await db.execute(
        select(PatternInsight).where(PatternInsight.pattern_id == pattern.id)
    )).scalars().all()
    for old in old_insights:
        await db.delete(old)

    for insight_data in result.get("insights", []):
        insight = PatternInsight(
            user_id=user_id,
            pattern_id=pattern.id,
            insight_type=insight_data.get("type", "recommendation"),
            category=insight_data.get("category", "clarity"),
            title=insight_data.get("title", ""),
            description=insight_data.get("description", ""),
            evidence=json.dumps(insight_data.get("evidence", []), ensure_ascii=False),
            suggested_practice=insight_data.get("suggested_practice"),
        )
        db.add(insight)

    await db.commit()
    await db.refresh(pattern)
    return pattern


async def get_pattern_trend(db: AsyncSession, user_id: int) -> dict:
    patterns = (await db.execute(
        select(CommunicationPattern)
        .where(CommunicationPattern.user_id == user_id)
        .order_by(CommunicationPattern.created_at)
    )).scalars().all()

    if not patterns:
        return {"periods": [], "dimensions": {}}

    periods = [p.last_computed_at.strftime("%Y-%m") if p.last_computed_at else "unknown" for p in patterns]
    dimension_keys = ["assertiveness", "empathy", "clarity", "adaptability", "conflict_handling", "active_listening"]
    dimensions = {k: [getattr(p, k) for p in patterns] for k in dimension_keys}

    return {"periods": periods, "dimensions": dimensions}