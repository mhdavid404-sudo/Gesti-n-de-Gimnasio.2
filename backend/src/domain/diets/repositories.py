"""Puertos (interfaces) del repositorio de Diets.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.diets.entities import DietAssignment, DietPlan


class DietPlanRepository(ABC):
    @abstractmethod
    def get_by_id(self, diet_plan_id: int) -> DietPlan | None: ...

    @abstractmethod
    def list_all(self) -> list[DietPlan]: ...

    @abstractmethod
    def add(self, diet_plan: DietPlan) -> DietPlan: ...

    @abstractmethod
    def update(self, diet_plan: DietPlan) -> DietPlan: ...

    @abstractmethod
    def delete(self, diet_plan_id: int) -> None: ...


class DietAssignmentRepository(ABC):
    @abstractmethod
    def get_by_id(self, assignment_id: int) -> DietAssignment | None: ...

    @abstractmethod
    def list_by_client(self, client_id: int) -> list[DietAssignment]: ...

    @abstractmethod
    def list_by_trainer(self, trainer_id: int) -> list[DietAssignment]: ...

    @abstractmethod
    def add(self, assignment: DietAssignment) -> DietAssignment: ...

    @abstractmethod
    def update(self, assignment: DietAssignment) -> DietAssignment: ...

    @abstractmethod
    def delete(self, assignment_id: int) -> None: ...
