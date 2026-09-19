"""Casos de uso del modulo Progress. Entrega 1: solo el esqueleto."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.progress.entities import BodyProgress
from src.domain.progress.repositories import BodyProgressRepository


@dataclass
class RegisterBodyProgressUseCase:
    """RF010: registrar progreso corporal (peso, medidas, fecha)."""

    progress_repository: BodyProgressRepository

    def execute(self, record: BodyProgress) -> BodyProgress:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class GetClientProgressTimelineUseCase:
    """RF011: obtener la evolucion de progreso corporal en el tiempo."""

    progress_repository: BodyProgressRepository

    def execute(self, client_id: int) -> list[BodyProgress]:
        raise NotImplementedError("Entrega 2: logica pendiente")
