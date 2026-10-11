"""Router FastAPI del modulo Progress (RF010, RF011).

Autorizacion por endpoint (mismo criterio ya decidido en los modulos
Ejercicios y Rutinas / Dietas, ver DECISIONES.md):

- `POST /progress`: `admin` o `entrenador` -- es una medicion que
  tipicamente toma el staff del gimnasio (bascula, cinta metrica), no un
  autoservicio del cliente. Si es `entrenador`,
  `RegisterBodyProgressUseCase` valida que el cliente sea suyo (403 si
  no). `cliente` queda bloqueado de entrada (RF013 es de solo lectura).
- `GET /progress/clients/{client_id}`: ownership por dato, mismo criterio
  que el resto del proyecto -- `admin` cualquiera; `entrenador` solo si
  el cliente es suyo; `cliente` solo el propio (RF011: el propio cliente
  necesita poder ver su evolucion, es la pestaña "Progreso" de
  `ClientDetailPage.tsx`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.progress import BodyProgressCreate, BodyProgressRead
from src.application.progress.use_cases import (
    GetClientProgressTimelineUseCase,
    RegisterBodyProgressUseCase,
)
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.progress.entities import BodyProgress
from src.domain.progress.exceptions import (
    InvalidBodyProgressWeightError,
    UnauthorizedBodyProgressRegistrationError,
)
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.progress import SqlAlchemyBodyProgressRepository

router = APIRouter(prefix="/progress", tags=["progress"])

_CLIENTE_NO_ENCONTRADO = "El cliente solicitado no existe."
_SIN_ACCESO_AL_HISTORIAL = "No tienes acceso al historial de este cliente."


@router.post(
    "",
    response_model=BodyProgressRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def register_body_progress(
    payload: BodyProgressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BodyProgressRead:
    """RF010: registrar progreso corporal (peso, medidas, fecha). Si es
    `entrenador`, `RegisterBodyProgressUseCase` valida que el cliente sea
    suyo. `cliente` bloqueado de entrada -- RF013 es de solo lectura."""
    progress_repository = SqlAlchemyBodyProgressRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = RegisterBodyProgressUseCase(
        progress_repository=progress_repository, client_repository=client_repository
    )

    try:
        created = use_case.execute(
            BodyProgress(
                id=None,
                client_id=payload.client_id,
                record_date=payload.record_date,
                weight_kg=payload.weight_kg,
                height_cm=payload.height_cm,
                body_fat_pct=payload.body_fat_pct,
                muscle_mass_kg=payload.muscle_mass_kg,
                chest_cm=payload.chest_cm,
                waist_cm=payload.waist_cm,
                hip_cm=payload.hip_cm,
                arm_cm=payload.arm_cm,
                notes=payload.notes,
            ),
            registrant_role=current_user.role,
            registrant_id=current_user.id,  # type: ignore[arg-type]
        )
    except ClientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente {exc.client_id} no existe.",
        ) from exc
    except InvalidBodyProgressWeightError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UnauthorizedBodyProgressRegistrationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return BodyProgressRead.model_validate(created)


@router.get("/clients/{client_id}", response_model=list[BodyProgressRead])
def get_client_progress_timeline(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BodyProgressRead]:
    """RF011: evolucion del progreso corporal en el tiempo (para el
    dashboard). Ownership por dato igual que el resto del proyecto:
    `admin` cualquiera; `entrenador` solo si el cliente es suyo; `cliente`
    solo el propio."""
    client_repository = SqlAlchemyClientProfileRepository(db)
    progress_repository = SqlAlchemyBodyProgressRepository(db)

    profile = client_repository.get_by_id(client_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO)

    if current_user.role == "entrenador" and profile.trainer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_AL_HISTORIAL)
    if current_user.role == "cliente" and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_AL_HISTORIAL)

    use_case = GetClientProgressTimelineUseCase(progress_repository=progress_repository)
    return [BodyProgressRead.model_validate(r) for r in use_case.execute(client_id)]
