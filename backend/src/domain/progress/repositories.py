"""Puerto (interfaz) del repositorio de Progress.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.progress.entities import BodyProgress


class BodyProgressRepository(ABC):
    @abstractmethod
    def get_by_id(self, record_id: int) -> BodyProgress | None: ...

    @abstractmethod
    def list_by_client(self, client_id: int) -> list[BodyProgress]:
        """Usado por RF011 (dashboard de evolucion en el tiempo)."""
        ...

    @abstractmethod
    def add(self, record: BodyProgress) -> BodyProgress: ...

    @abstractmethod
    def update(self, record: BodyProgress) -> BodyProgress: ...

    @abstractmethod
    def delete(self, record_id: int) -> None: ...
