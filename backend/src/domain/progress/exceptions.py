"""Excepciones de dominio del modulo Progress.

`ClientNotFoundError` NO se duplica aqui -- se reusa la de
`domain.clients.exceptions` (mismo criterio ya aplicado por
`AssignMembershipUseCase`/`RegisterPaymentUseCase`/
`AssignRoutineToClientUseCase`/`AssignDietToClientUseCase`: el cliente
inexistente es siempre el mismo caso real, un solo tipo de excepcion en
todo el proyecto, ver DECISIONES.md).

Este modulo solo agrega las excepciones que le son exclusivas: el
ownership de entrenador sobre el cliente al registrar un progreso, y la
validacion defensiva de `weight_kg` (el dominio no confia ciegamente en
que la capa de transporte ya valido `gt=0`, mismo criterio aplicado en
Pagos).
"""

from __future__ import annotations


class UnauthorizedBodyProgressRegistrationError(Exception):
    """Un `entrenador` intento registrar progreso corporal de un cliente
    que no tiene asignado (`ClientProfile.trainer_id != assigner_id`).
    """

    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        super().__init__(
            f"El cliente {client_id} no esta asignado a este entrenador"
        )


class InvalidBodyProgressWeightError(Exception):
    """`weight_kg` no es positivo.

    Validacion defensiva: el schema de transporte (`BodyProgressCreate`)
    ya declara `Field(gt=0)`, pero el dominio no debe confiar ciegamente
    en que todo caller pase siempre por esa capa (mismo criterio aplicado
    en el modulo Pagos).
    """

    def __init__(self, weight_kg: object) -> None:
        self.weight_kg = weight_kg
        super().__init__(f"weight_kg debe ser positivo, recibido: {weight_kg!r}")
