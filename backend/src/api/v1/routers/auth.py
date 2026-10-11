"""Router FastAPI del modulo Auth (RF001: login).

El JWT se genera aqui, NUNCA en `application/users/use_cases.py` -- el
dominio/aplicacion no debe saber que una sesion se representa como un
token. `AuthenticateUserUseCase` solo verifica credenciales.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.schemas.auth import LoginRequest, TokenResponse
from src.api.v1.schemas.users import UserRead
from src.application.users.use_cases import AuthenticateUserUseCase
from src.domain.users.exceptions import InvalidCredentialsError
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.security.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

_CREDENCIALES_INVALIDAS = "Email o password incorrectos."


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """RF001: autenticar un usuario y emitir un JWT de sesion."""
    repository = SqlAlchemyUserRepository(db)
    use_case = AuthenticateUserUseCase(user_repository=repository)

    try:
        user = use_case.execute(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_CREDENCIALES_INVALIDAS,
        ) from exc

    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))
