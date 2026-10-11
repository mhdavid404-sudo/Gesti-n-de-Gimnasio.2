"""Paquete de infraestructura de seguridad (hashing de password, JWT).

Regla dura (DECISIONES.md, correccion #2): este paquete vive en
`infrastructure/`, nunca en `domain/`. El dominio (`domain/users/*`) no
sabe que existe bcrypt ni JWT -- solo conoce `password_hash: str` como un
campo opaco de la entidad `User`. Los casos de uso en `application/` son
quienes llaman a `hash_password`/`verify_password` (inyectados, no
importados directo desde el dominio).
"""

from __future__ import annotations
