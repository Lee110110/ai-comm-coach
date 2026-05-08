import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.simulation import SimulationSession, SimulationMessage
from app.schemas.simulation import (
    SimulationCreate, SimulationMessageSend, DifficultyUpdate,
    SimulationMessageOut, SimulationOut, DebriefOut, Feedback,
)
from app.services.simulation_service import create_simulation, send_simulation_message, end_simulation

router = APIRouter(prefix="/simulations", tags=["模拟演练"])


@router.post("", response_model=SimulationOut)
async def create_sim(
    data: SimulationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await create_simulation(db, current_user.id, data.model_dump())
    return SimulationOut.model_validate(session)


@router.get("", response_model=list[SimulationOut])
async def list_simulations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.user_id == current_user.id)
        .order_by(SimulationSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [SimulationOut.model_validate(s) for s in sessions]


@router.get("/{session_id}")
async def get_simulation(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id, SimulationSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="模拟会话不存在")

    msg_result = await db.execute(
        select(SimulationMessage)
        .where(SimulationMessage.session_id == session_id)
        .order_by(SimulationMessage.turn_number)
    )
    messages = msg_result.scalars().all()

    msg_out = []
    for m in messages:
        feedback = None
        if m.feedback:
            try:
                fb_data = json.loads(m.feedback)
                feedback = Feedback(**fb_data)
            except Exception:
                pass
        msg_out.append(SimulationMessageOut(
            id=m.id, role=m.role, content=m.content,
            feedback=feedback, turn_number=m.turn_number, created_at=m.created_at,
        ))

    return {
        **SimulationOut.model_validate(session).model_dump(),
        "messages": msg_out,
    }


@router.post("/{session_id}/messages", response_model=SimulationMessageOut)
async def send_message(
    session_id: int,
    data: SimulationMessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id, SimulationSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="模拟会话不存在")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="会话已结束")

    assistant_msg = await send_simulation_message(db, session, data.content)

    feedback = None
    if assistant_msg.feedback:
        try:
            fb_data = json.loads(assistant_msg.feedback)
            feedback = Feedback(**fb_data)
        except Exception:
            pass

    return SimulationMessageOut(
        id=assistant_msg.id, role=assistant_msg.role, content=assistant_msg.content,
        feedback=feedback, turn_number=assistant_msg.turn_number, created_at=assistant_msg.created_at,
    )


@router.put("/{session_id}/difficulty")
async def update_difficulty(
    session_id: int,
    data: DifficultyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id, SimulationSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="模拟会话不存在")

    session.difficulty = data.difficulty
    await db.commit()
    return {"difficulty": data.difficulty}


@router.post("/{session_id}/end", response_model=DebriefOut)
async def end_sim(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id, SimulationSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="模拟会话不存在")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="会话已结束")

    debrief = await end_simulation(db, session)

    return DebriefOut(
        overall_score=debrief.get("overall_score", 0),
        summary=debrief.get("summary", ""),
        strengths=debrief.get("strengths", []),
        improvements=debrief.get("improvements", []),
        dimension_scores=debrief.get("dimension_scores", {}),
        recommended_practice=debrief.get("recommended_practice", ""),
    )


@router.get("/{session_id}/debrief", response_model=DebriefOut)
async def get_debrief(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SimulationSession)
        .where(SimulationSession.id == session_id, SimulationSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="模拟会话不存在")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="会话尚未结束")

    return DebriefOut(
        overall_score=session.overall_score or 0,
        summary=json.loads(session.debrief_summary) if session.debrief_summary else "",
        strengths=json.loads(session.strengths) if session.strengths else [],
        improvements=json.loads(session.improvements) if session.improvements else [],
        dimension_scores=json.loads(session.dimension_scores) if session.dimension_scores else {},
        recommended_practice=session.recommended_practice or "",
    )