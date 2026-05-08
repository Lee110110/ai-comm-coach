from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.message import MessagePolish
from app.schemas.message import MessagePolishRequest, MessagePolishOut
from app.services.message_service import polish_message, format_message_out

router = APIRouter(prefix="/messages", tags=["消息润色"])


@router.post("/polish", response_model=MessagePolishOut)
async def polish(
    data: MessagePolishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    msg = await polish_message(db, current_user.id, data.model_dump())
    return format_message_out(msg)


@router.get("", response_model=list[MessagePolishOut])
async def list_messages(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MessagePolish)
        .where(MessagePolish.user_id == current_user.id)
        .order_by(MessagePolish.created_at.desc())
    )
    messages = result.scalars().all()
    return [format_message_out(m) for m in messages]


@router.get("/{message_id}", response_model=MessagePolishOut)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MessagePolish).where(MessagePolish.id == message_id, MessagePolish.user_id == current_user.id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="记录不存在")
    return format_message_out(msg)


@router.delete("/{message_id}", status_code=204)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MessagePolish).where(MessagePolish.id == message_id, MessagePolish.user_id == current_user.id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="记录不存在")
    await db.delete(msg)
    await db.commit()