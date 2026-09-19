"""Agrega todos los routers de v1 bajo un solo `APIRouter`.

`api/main.py` monta este router bajo el prefijo `/api/v1`.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.v1.routers.clients import router as clients_router
from src.api.v1.routers.diets import router as diets_router
from src.api.v1.routers.memberships import plans_router as membership_plans_router
from src.api.v1.routers.memberships import router as memberships_router
from src.api.v1.routers.notifications import audit_router as audit_logs_router
from src.api.v1.routers.notifications import router as notifications_router
from src.api.v1.routers.payments import router as payments_router
from src.api.v1.routers.progress import router as progress_router
from src.api.v1.routers.routines import exercises_router
from src.api.v1.routers.routines import router as routines_router
from src.api.v1.routers.users import router as users_router

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(clients_router)
api_router.include_router(membership_plans_router)
api_router.include_router(memberships_router)
api_router.include_router(payments_router)
api_router.include_router(exercises_router)
api_router.include_router(routines_router)
api_router.include_router(diets_router)
api_router.include_router(progress_router)
api_router.include_router(notifications_router)
api_router.include_router(audit_logs_router)
