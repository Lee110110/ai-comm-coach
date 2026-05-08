from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.simulations import router as simulations_router
from app.api.v1.messages import router as messages_router
from app.api.v1.patterns import router as patterns_router
from app.api.v1.relationships import router as relationships_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(scenarios_router)
router.include_router(simulations_router)
router.include_router(messages_router)
router.include_router(patterns_router)
router.include_router(relationships_router)