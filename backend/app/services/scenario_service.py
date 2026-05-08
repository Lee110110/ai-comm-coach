import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scenario import Scenario
from app.services.llm_service import llm_service
from app.services.prompt_templates import SCENARIO_SYSTEM, SCENARIO_USER

logger = logging.getLogger(__name__)


async def create_scenario_with_advice(
    db: AsyncSession,
    user_id: int,
    data: dict,
) -> Scenario:
    relationship_type = data.get("relationship_type", "未指定")
    context = data.get("context") or "无"

    prompt = SCENARIO_USER.format(
        title=data["title"],
        description=data["description"],
        context=context,
        relationship_type=relationship_type,
        urgency=data.get("urgency", "medium"),
    )

    result, input_tokens, output_tokens = await llm_service.call_json(
        messages=[
            {"role": "system", "content": SCENARIO_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    strategies = result.get("strategies", {})
    scenario = Scenario(
        user_id=user_id,
        relationship_id=data.get("relationship_id"),
        title=data["title"],
        description=data["description"],
        context=data.get("context"),
        relationship_type=relationship_type,
        urgency=data.get("urgency", "medium"),
        strategy_gentle=json.dumps(strategies.get("gentle"), ensure_ascii=False) if strategies.get("gentle") else None,
        strategy_direct=json.dumps(strategies.get("direct"), ensure_ascii=False) if strategies.get("direct") else None,
        strategy_strategic=json.dumps(strategies.get("strategic"), ensure_ascii=False) if strategies.get("strategic") else None,
        pitfalls=json.dumps(result.get("pitfalls"), ensure_ascii=False),
        predicted_reactions=json.dumps(result.get("predicted_reactions"), ensure_ascii=False),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return scenario


def format_scenario_out(scenario: Scenario) -> dict:
    strategies = {}
    if scenario.strategy_gentle:
        strategies["gentle"] = json.loads(scenario.strategy_gentle)
    if scenario.strategy_direct:
        strategies["direct"] = json.loads(scenario.strategy_direct)
    if scenario.strategy_strategic:
        strategies["strategic"] = json.loads(scenario.strategy_strategic)

    pitfalls = json.loads(scenario.pitfalls) if scenario.pitfalls else None
    predicted_reactions = json.loads(scenario.predicted_reactions) if scenario.predicted_reactions else None

    return {
        "id": scenario.id,
        "title": scenario.title,
        "description": scenario.description,
        "context": scenario.context,
        "relationship_type": scenario.relationship_type,
        "urgency": scenario.urgency,
        "strategies": strategies or None,
        "pitfalls": pitfalls,
        "predicted_reactions": predicted_reactions,
        "created_at": scenario.created_at,
    }