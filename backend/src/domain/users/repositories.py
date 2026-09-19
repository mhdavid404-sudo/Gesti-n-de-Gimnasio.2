"""Puerto (interfaz) del repositorio de Users.

Regla dura (DECISIONES.md, correccion #3): esta interfaz habla en terminos
de entidades de dominio (`User`) nada mas. JAMAS recibe ni devuelve un
`Session` de SQLAlchemy ni ningun otro objeto de infraestructura. La
implementacion concreta (con SQLAlchemy) vive en
`infrastructure/repositories/users.py` y es la unica pieza que conoce el
detalle de persistencia.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.users.entities import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def list_by_role(self, role: str) -> list[User]: ...

    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def delete(self, user_id: int) -> None: ...
