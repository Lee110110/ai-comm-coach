import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simulation import SimulationSession, SimulationMessage
from app.services.llm_service import llm_service
from app.services.prompt_templates import (
    SIMULATION_ROLE_SYSTEM,
    SIMULATION_DIFFICULTY,
    SIMULATION_FEEDBACK_SYSTEM,
    SIMULATION_DEBRIEF_SYSTEM,
)

logger = logging.getLogger(__name__)


async def create_simulation(
    db: AsyncSession,
    user_id: int,
    data: dict,
) -> SimulationSession:
    role_desc = data.get("role_description") or "你的对话对象"
    difficulty = data.get("difficulty", "medium")

    session = SimulationSession(
        user_id=user_id,
        relationship_id=data.get("relationship_id"),
        scenario_description=data["scenario_description"],
        role_description=role_desc,
        difficulty=difficulty,
        status="active",
    )

    difficulty_instruction = SIMULATION_DIFFICULTY.get(difficulty, SIMULATION_DIFFICULTY["medium"])
    system_prompt = SIMULATION_ROLE_SYSTEM.format(
        role_description=role_desc,
        scenario_description=data["scenario_description"],
        difficulty_instruction=difficulty_instruction,
    )

    opening_result, input_tokens, output_tokens = await llm_service.call_json(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "模拟开始，请你先开口说话。"},
        ],
        temperature=0.8,
    )

    session.input_tokens += input_tokens
    session.output_tokens += output_tokens

    db.add(session)
    await db.commit()
    await db.refresh(session)

    opening_msg = SimulationMessage(
        session_id=session.id,
        role="assistant",
        content=opening_result.get("reply", "你好，我们聊聊吧。"),
        turn_number=0,
    )
    db.add(opening_msg)

    session.turn_count = 1
    await db.commit()
    await db.refresh(session)

    return session


async def send_simulation_message(
    db: AsyncSession,
    session: SimulationSession,
    user_content: str,
) -> SimulationMessage:
    difficulty_instruction = SIMULATION_DIFFICULTY.get(session.difficulty, SIMULATION_DIFFICULTY["medium"])
    system_prompt = SIMULATION_ROLE_SYSTEM.format(
        role_description=session.role_description or "你的对话对象",
        scenario_description=session.scenario_description,
        difficulty_instruction=difficulty_instruction,
    )

    result_msgs = await db.execute(
        select(SimulationMessage)
        .where(SimulationMessage.session_id == session.id)
        .order_by(SimulationMessage.turn_number)
    )
    history = result_msgs.scalars().all()

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_content})

    user_msg = SimulationMessage(
        session_id=session.id,
        role="user",
        content=user_content,
        turn_number=session.turn_count,
    )
    db.add(user_msg)

    role_result, role_in, role_out = await llm_service.call_json(
        messages=messages,
        temperature=0.8,
    )
    session.input_tokens += role_in
    session.output_tokens += role_out

    assistant_reply = role_result.get("reply", "嗯，我理解你的意思。")

    feedback_data = None
    try:
        conversation_history = "\n".join(
            f"{'用户' if m.role == 'user' else '对方'}：{m.content}" for m in history[-6:]
        )
        feedback_prompt = SIMULATION_FEEDBACK_SYSTEM.format(
            scenario_description=session.scenario_description,
            conversation_history=conversation_history,
            user_message=user_content,
            assistant_reply=assistant_reply,
        )
        feedback_result, fb_in, fb_out = await llm_service.call_json(
            messages=[{"role": "system", "content": feedback_prompt}],
            temperature=0.3,
        )
        feedback_data = feedback_result
        session.input_tokens += fb_in
        session.output_tokens += fb_out
    except Exception as e:
        logger.warning(f"Feedback generation failed: {e}")

    assistant_msg = SimulationMessage(
        session_id=session.id,
        role="assistant",
        content=assistant_reply,
        feedback=json.dumps(feedback_data, ensure_ascii=False) if feedback_data else None,
        turn_number=session.turn_count + 1,
    )
    db.add(assistant_msg)

    session.turn_count += 2
    await db.commit()
    await db.refresh(assistant_msg)

    return assistant_msg


async def end_simulation(
    db: AsyncSession,
    session: SimulationSession,
) -> dict:
    result_msgs = await db.execute(
        select(SimulationMessage)
        .where(SimulationMessage.session_id == session.id)
        .order_by(SimulationMessage.turn_number)
    )
    messages = result_msgs.scalars().all()

    full_conversation = "\n".join(
        f"{'用户' if m.role == 'user' else '对方'}：{m.content}" for m in messages
    )

    debrief_prompt = SIMULATION_DEBRIEF_SYSTEM.format(
        scenario_description=session.scenario_description,
        full_conversation=full_conversation,
    )

    debrief, debrief_in, debrief_out = await llm_service.call_json(
        messages=[{"role": "system", "content": debrief_prompt}],
        temperature=0.3,
    )

    session.status = "completed"
    session.overall_score = debrief.get("overall_score", 0)
    session.debrief_summary = json.dumps(debrief.get("summary"), ensure_ascii=False)
    session.strengths = json.dumps(debrief.get("strengths"), ensure_ascii=False)
    session.improvements = json.dumps(debrief.get("improvements"), ensure_ascii=False)
    session.dimension_scores = json.dumps(debrief.get("dimension_scores"), ensure_ascii=False)
    session.recommended_practice = debrief.get("recommended_practice", "")
    session.input_tokens += debrief_in
    session.output_tokens += debrief_out

    await db.commit()
    await db.refresh(session)

    return debrief