"""Puerto (interfaz) del repositorio de Clients.

Habla solo en terminos de `ClientProfile` (DECISIONES.md, correccion #3).
Ningun metodo recibe/devuelve una `Session` de SQLAlchemy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.clients.entities import ClientProfile


class ClientProfileRepository(ABC):
    @abstractmethod
    def get_by_id(self, client_id: int) -> ClientProfile | None: ...

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> ClientProfile | None: ...

    @abstractmethod
    def list_by_trainer(self, trainer_id: int) -> list[ClientProfile]: ...

    @abstractmethod
    def list_all(self) -> list[ClientProfile]: ...

    @abstractmethod
    def add(self, client: ClientProfile) -> ClientProfile: ...

    @abstractmethod
    def update(self, client: ClientProfile) -> ClientProfile: ...

    @abstractmethod
    def delete(self, client_id: int) -> None: ...
