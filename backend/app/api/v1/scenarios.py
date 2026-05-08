from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioOut, ScenarioListItem
from app.services.scenario_service import create_scenario_with_advice, format_scenario_out

router = APIRouter(prefix="/scenarios", tags=["急救话术"])


@router.post("", response_model=ScenarioOut)
async def create_scenario(
    data: ScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scenario = await create_scenario_with_advice(db, current_user.id, data.model_dump())
    return format_scenario_out(scenario)


@router.get("", response_model=list[ScenarioListItem])
async def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario)
        .where(Scenario.user_id == current_user.id)
        .order_by(Scenario.created_at.desc())
    )
    scenarios = result.scalars().all()
    return [ScenarioListItem.model_validate(s) for s in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    return format_scenario_out(scenario)


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    await db.delete(scenario)
    await db.commit()