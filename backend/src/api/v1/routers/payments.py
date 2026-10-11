"""Router FastAPI del modulo Payments (RF005).

Autorizacion por endpoint (criterio decidido en esta entrada de Entrega 2
del modulo Pagos, ver DECISIONES.md):

- `POST /payments` (registrar un pago): solo `admin` -- registrar un pago es
  una decision administrativa/financiera, mismo criterio que el alta de
  cliente (`POST /clients`) y la asignacion de membresia (`POST
  /memberships`) en los modulos anteriores.
- `GET /payments` (listado, filtro opcional `membership_id` en query) y
  `GET /payments/{id}`: ownership por dato ENCADENADO -- un nivel mas
  profundo que `GET /memberships/{id}`. El dueno real de un `Payment` no es
  directo: hay que resolver `Payment.membership_id` -> `Membership.client_id`
  -> `ClientProfile` para saber a quien pertenece.
    - `admin`: ve todos, o filtra por `membership_id` si lo manda en query.
    - `entrenador`: solo los pagos de membresias de SUS clientes asignados
      (resueltos via `ClientProfileRepository.list_by_trainer` ->
      `MembershipRepository.list_by_client` -> `PaymentRepository.
      list_by_membership`, encadenando los 3 repositorios).
    - `cliente`: solo los suyos propios (mismo encadenado, resolviendo su
      `client_id` via `ClientProfileRepository.get_by_user_id`).
  El `membership_id` de query se ignora para `entrenador`/`cliente` si no
  corresponde a una membresia propia -- nunca ven pagos ajenos.

No hay `PATCH`/`DELETE /payments/{id}` en el esqueleto original -- no se
agrega ninguno, fuera de alcance de este encargo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.payments import PaymentCreate, PaymentRead
from src.application.payments.use_cases import RegisterPaymentUseCase
from src.domain.memberships.exceptions import MembershipNotFoundError
from src.domain.payments.entities import Payment
from src.domain.payments.exceptions import (
    InvalidPaymentMethodError,
    InvalidPaymentStatusError,
)
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.memberships import SqlAlchemyMembershipRepository
from src.infrastructure.repositories.payments import SqlAlchemyPaymentRepository

router = APIRouter(prefix="/payments", tags=["payments"])

_PAGO_NO_ENCONTRADO = "El pago solicitado no existe."
_SIN_ACCESO_A_PAGO = "No tienes acceso a este pago."


def _resolve_own_membership_ids(
    current_user: User,
    client_repository: SqlAlchemyClientProfileRepository,
    membership_repository: SqlAlchemyMembershipRepository,
) -> list[int] | None:
    """Resuelve, para `entrenador`/`cliente`, la lista de `membership_id`
    que les pertenecen (encadenando `ClientProfile` -> `Membership`).
    Devuelve `None` para `admin` (sin restriccion)."""
    if current_user.role == "entrenador":
        own_client_ids = [
            profile.id for profile in client_repository.list_by_trainer(current_user.id)  # type: ignore[arg-type]
        ]
    elif current_user.role == "cliente":
        own_profile = client_repository.get_by_user_id(current_user.id)  # type: ignore[arg-type]
        own_client_ids = [own_profile.id] if own_profile is not None else []
    else:
        return None

    memberships = [
        m for cid in own_client_ids for m in membership_repository.list_by_client(cid)  # type: ignore[arg-type]
    ]
    return [m.id for m in memberships if m.id is not None]


@router.post(
    "",
    response_model=PaymentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def register_payment(
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentRead:
    """RF005: registrar un pago asociado a la membresia de un cliente.

    Solo `admin`. `registered_by` NUNCA viene del body (ver correccion de
    seguridad en `api/v1/schemas/payments.py`) -- se rellena siempre con el
    `id` del admin autenticado que hace la peticion.
    """
    payment_repository = SqlAlchemyPaymentRepository(db)
    membership_repository = SqlAlchemyMembershipRepository(db)
    use_case = RegisterPaymentUseCase(
        payment_repository=payment_repository,
        membership_repository=membership_repository,
    )

    try:
        created = use_case.execute(
            Payment(
                id=None,
                membership_id=payload.membership_id,
                amount=payload.amount,
                payment_date=payload.payment_date,
                method=payload.method,
                status=payload.status,
                registered_by=current_user.id,  # type: ignore[arg-type]
                notes=payload.notes,
            )
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La membresia {exc.membership_id} no existe.",
        ) from exc
    except (InvalidPaymentMethodError, InvalidPaymentStatusError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return PaymentRead.model_validate(created)


@router.get("", response_model=list[PaymentRead])
def list_payments(
    membership_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaymentRead]:
    """Ownership por dato encadenado -- ver docstring del modulo arriba."""
    payment_repository = SqlAlchemyPaymentRepository(db)
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)

    own_membership_ids = _resolve_own_membership_ids(
        current_user, client_repository, membership_repository
    )

    if own_membership_ids is None:  # admin
        if membership_id is not None:
            target_membership_ids = [membership_id]
        else:
            all_client_ids = [profile.id for profile in client_repository.list_all()]
            target_membership_ids = [
                m.id
                for cid in all_client_ids
                for m in membership_repository.list_by_client(cid)  # type: ignore[arg-type]
                if m.id is not None
            ]
    else:
        if membership_id is not None and membership_id in own_membership_ids:
            target_membership_ids = [membership_id]
        else:
            target_membership_ids = own_membership_ids

    payments = [
        p for mid in target_membership_ids for p in payment_repository.list_by_membership(mid)
    ]
    return [PaymentRead.model_validate(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentRead:
    """Mismo criterio de ownership por dato encadenado que el listado."""
    payment_repository = SqlAlchemyPaymentRepository(db)
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)

    payment = payment_repository.get_by_id(payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PAGO_NO_ENCONTRADO)

    own_membership_ids = _resolve_own_membership_ids(
        current_user, client_repository, membership_repository
    )
    if own_membership_ids is not None and payment.membership_id not in own_membership_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_PAGO)

    return PaymentRead.model_validate(payment)
