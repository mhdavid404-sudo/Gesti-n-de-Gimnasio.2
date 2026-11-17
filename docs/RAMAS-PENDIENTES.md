# Ramas remotas pendientes de otros integrantes

Fecha de verificación: 2026-11-16. Metodología: `git fetch --all`, luego
`git log main..origin/<rama>` (commits únicos de la rama, no en `main`) y
`git merge-tree --write-tree main origin/<rama>` (fusión de prueba, **sin
guardar nada, sin escribir ningún commit ni mover ninguna referencia**) para
detectar conflictos reales. Ninguna rama se tocó, modificó ni fusionó.

| Rama | Autor del último commit | Archivos que toca (únicos, no en `main`) | ¿Conflicto con `main`? | Notas |
|---|---|---|---|---|
| `origin/datos/cristobal` | mhdavid404-sudo (mismo usuario que `main`) | Ninguno — 0 commits únicos | No aplica | La rama apunta a un commit que ya es ancestro de `main` (quedó atrás, nunca se le agregó trabajo propio de Cristóbal Gómez Jorge Alejandro, Analista de Datos según la Tabla 4 del documento). |
| `origin/docs/espinosa` | mhdavid404-sudo (mismo usuario que `main`) | Ninguno — 0 commits únicos | No aplica | Mismo caso que arriba — rama placeholder sin trabajo propio de Espinosa Medina Luis Layonet. |
| `origin/pruebas-manuales/luna` | mhdavid404-sudo (mismo usuario que `main`) | Ninguno — 0 commits únicos | No aplica | Mismo caso — sin trabajo propio de Luna Luna Marcos Augusto. |
| `origin/pruebas/delacruz` | benjamindlcg79 (Benjamín De La Cruz Ramírez, Control de Calidad/Monitor según la Tabla 4) | `DOCS/Casos-de-Uso-SmartGym-v2.docx`, `DOCS/Plan-de-Pruebas-SmartGym-v2.docx` (1 commit: "Agrego plan de pruebas y casos de uso") | **No a nivel Git** (`git merge-tree` resuelve sin marcadores de conflicto) — **sí hay un problema real a nivel de sistema de archivos**: ver nota abajo. | |

## Nota sobre `pruebas/delacruz`: mismo contenido, carpeta con otra mayúscula

`main` ya tiene `docs/Casos-de-Uso-SmartGym-v2.docx` y
`docs/Plan-de-Pruebas-SmartGym-v2.docx` (minúscula `docs/`, agregados en una
sesión de trabajo previa). La rama de Benjamín agrega los mismos dos
archivos bajo `DOCS/` (mayúscula). Git trata ambas rutas como distintas (es
case-sensitive internamente), así que una fusión real no marcaría conflicto
-- pero en un checkout de Windows o macOS (sistema de archivos
case-insensitive por defecto, como el que usa este equipo) **las dos
carpetas colisionan en el mismo directorio físico**, lo que puede dejar el
working tree en un estado inconsistente según el orden de extracción. No se
fusiona esta rama. Si se quiere incorporar su trabajo más adelante, el paso
correcto es pedirle a Benjamín que renombre su carpeta a `docs/` (minúscula)
antes de abrir un PR, o fusionar manualmente solo el contenido (que ya
coincide con lo que `main` tiene) descartando la carpeta duplicada.

## Bugs abiertos encontrados en las ramas

Ninguno — las 3 ramas placeholder no tienen contenido propio que revisar, y
la rama de Benjamín solo agrega 2 archivos `.docx` ya presentes en `main`
(contenido idéntico, verificado en la auditoría de `docs/AUDITORIA-DOC-VS-CODIGO.md`).
