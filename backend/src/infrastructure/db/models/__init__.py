"""Importa todos los modelos SQLAlchemy para que `Base.metadata` los
conozca (usado por Alembic en `infrastructure/migrations/env.py`).
"""

from src.infrastructure.db.models.clients import ClientProfileModel
from src.infrastructure.db.models.diets import DietAssignmentModel, DietPlanModel
from src.infrastructure.db.models.memberships import MembershipModel, MembershipPlanModel
from src.infrastructure.db.models.notifications import AuditLogModel, NotificationModel
from src.infrastructure.db.models.payments import PaymentModel
from src.infrastructure.db.models.progress import BodyProgressModel
from src.infrastructure.db.models.routines import (
    ExerciseModel,
    RoutineAssignmentModel,
    RoutineExerciseModel,
    RoutineModel,
)
from src.infrastructure.db.models.users import UserModel

__all__ = [
    "UserModel",
    "ClientProfileModel",
    "MembershipPlanModel",
    "MembershipModel",
    "PaymentModel",
    "ExerciseModel",
    "RoutineModel",
    "RoutineExerciseModel",
    "RoutineAssignmentModel",
    "DietPlanModel",
    "DietAssignmentModel",
    "BodyProgressModel",
    "NotificationModel",
    "AuditLogModel",
]
