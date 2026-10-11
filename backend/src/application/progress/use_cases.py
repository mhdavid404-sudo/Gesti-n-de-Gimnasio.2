"""Casos de uso del modulo Progress (RF010, RF011).

Entrega 2: logica real, antes `NotImplementedError` (ver DECISIONES.md).
Modulo deliberadamente mas simple que Rutinas/Dietas: `BodyProgress` no
tiene ningun campo de autoria (`created_by`/`registered_by`/`assigned_by`)
-- no hay defecto de seguridad de ese tipo que corregir aqui, ni
invariante de rol de creador que validar. Solo hay ownership de
entrenador sobre el `client_id` al REGISTRAR (no hay "plan" ni
"asignacion" intermedios como en Rutinas/Dietas).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.progress.entities import BodyProgress
from src.domain.progress.exceptions import (
    InvalidBodyProgressWeightError,
    UnauthorizedBodyProgressRegistrationError,
)
from src.domain.progress.repositories import BodyProgressRepository


@dataclass
class RegisterBodyProgressUseCase:
    """RF010: registrar progreso corporal (peso, medidas, fecha).

    Valida, en este orden:
    1. que el cliente exista (`ClientNotFoundError`, reusada de
       `domain.clients.exceptions` -- mismo criterio ya aplicado por
       `AssignMembershipUseCase`/`AssignRoutineToClientUseCase`/
       `AssignDietToClientUseCase`).
    2. que `weight_kg` sea positivo (`InvalidBodyProgressWeightError`) --
       validacion defensiva: el schema de transporte ya exige
       `Field(gt=0)`, pero el dominio no confia ciegamente en eso (mismo
       criterio aplicado en Pagos).
    3. si quien registra es `entrenador`, que el cliente este asignado a
       EL (`UnauthorizedBodyProgressRegistrationError` si no) -- mismo
       patron de ownership que `AssignRoutineToClientUseCase`/
       `AssignDietToClientUseCase`.

    `registrant_role`/`registrant_id` representan a quien registra (ya
    resueltos server-side via `current_user` en el router, igual que
    `assigner_role`/`assigner_id` en Rutinas/Dietas) -- se pasan como
    parametros de `execute()` en vez de resolverse aqui adentro, mismo
    diseño ya usado por `AssignDietToClientUseCase.execute`.
    """

    progress_repository: BodyProgressRepository
    client_repository: ClientProfileRepository

    def execute(
        self,
        record: BodyProgress,
        registrant_role: str,
        registrant_id: int,
    ) -> BodyProgress:
        client = self.client_repository.get_by_id(record.client_id)
        if client is None:
            raise ClientNotFoundError(record.client_id)

        if record.weight_kg is None or record.weight_kg <= 0:
            raise InvalidBodyProgressWeightError(record.weight_kg)

        if registrant_role == "entrenador" and client.trainer_id != registrant_id:
            raise UnauthorizedBodyProgressRegistrationError(record.client_id)

        return self.progress_repository.add(record)


@dataclass
class GetClientProgressTimelineUseCase:
    """RF011: obtener la evolucion de progreso corporal en el tiempo.

    Trivial -- la diferencia de alcance por rol (admin cualquiera,
    entrenador solo sus clientes, cliente solo lo propio) es
    responsabilidad del ROUTER (ownership por dato, mismo criterio que
    `GetClientDietHistoryUseCase`/`GetClientRoutineHistoryUseCase`), no de
    este caso de uso.
    """

    progress_repository: BodyProgressRepository

    def execute(self, client_id: int) -> list[BodyProgress]:
        return self.progress_repository.list_by_client(client_id)
