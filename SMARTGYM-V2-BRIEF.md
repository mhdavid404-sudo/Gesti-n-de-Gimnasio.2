# SmartGym v2 — Brief de Proyecto (traspaso de contexto)

Este documento resume todo lo decidido hasta ahora para que un chat nuevo,
Claude Code, o cualquier agente del equipo tenga contexto completo sin
necesidad de repetir la conversación original. Última actualización: brief
v2, tras cerrar Apartado I, Apartado II y los RF (Apartado III).

## Qué es este proyecto

Reconstrucción completa de SmartGym (proyecto de gimnasio inteligente) desde
cero — no es un parche sobre el código viejo (`Gimnasio-inteligente-hexagonal`,
que era Flask + SQL Server). Esta vez se sube de nivel de stack y de
arquitectura, reutilizando solo el conocimiento del dominio, no el código.
Es diseño nuevo con documentación nueva (Apartado I a V, siguiendo la
plantilla oficial de la materia).

## El negocio real detrás del sistema (Apartado I)

- **Nombre:** Stronger Aragón, un gimnasio real
- **Cómo opera hoy:** todo el registro de clientes, membresías y pagos se
  lleva en Excel, gestionado por separado por cada recepcionista según su
  turno (una en la mañana, otra en la tarde/noche)
- **Problema real:** falta de control centralizado, no se sabe en tiempo
  real quién tiene un pago pendiente o membresía vencida, inconsistencias
  entre lo que registra cada turno
- **Por qué el sistema:** centralizar la información entre turnos, dar
  velocidad y control real a la administración

## Stack decidido

- Backend: Python 3.13, FastAPI, PostgreSQL
- Frontend: React + Vite + TypeScript
- Arquitectura: Hexagonal (dominio nunca depende de infraestructura) — mismo
  patrón que ATLAS y RETO1
- Contenedores: Docker + docker-compose

## Requerimientos Funcionales (Apartado III, cerrados)

| ID | Requisito | Prioridad |
|---|---|---|
| RF001 | Registrar e iniciar sesión de usuarios con roles diferenciados (Admin, Entrenador, Cliente). | Alta |
| RF002 | Restringir el acceso a funciones según el rol del usuario autenticado. | Alta |
| RF003 | Registrar, consultar, editar y eliminar clientes (CRUD) con sus datos de perfil. | Alta |
| RF004 | Asignar una membresía a cada cliente, con distintos planes (Básica/VIP/Premium). | Alta |
| RF005 | Registrar pagos asociados a la membresía de un cliente. | Alta |
| RF006 | Detectar y notificar membresías vencidas o próximas a vencer. | Media |
| RF007 | Crear y asignar rutinas de ejercicio a un cliente. | Alta |
| RF008 | Consultar el historial de rutinas asignadas a un cliente. | Media |
| RF009 | Crear y asignar planes de dieta a un cliente. | Media |
| RF010 | Registrar el progreso corporal del cliente (peso, medidas, fecha de registro). | Alta |
| RF011 | Mostrar un dashboard con la evolución del progreso corporal del cliente en el tiempo. | Alta |
| RF012 | Permitir que el Entrenador consulte y actualice rutinas/dietas de los clientes que tiene asignados. | Media |
| RF013 | Permitir que el Cliente consulte su propia información (rutina, dieta, progreso, membresía) sin poder modificarla. | Alta |
| RF014 | Exponer las funciones anteriores mediante una API REST documentada. | Alta |
| RF015 | Registrar errores y eventos relevantes del sistema en una bitácora de logs. | Media |

## Equipo y roles (Apartado 2.2)

| Integrante | Rol Asignado | Responsabilidades |
|---|---|---|
| Manzano Hernández David Axel | Líder de Proyecto | Coordinación, desarrollo técnico completo, seguimiento en Planner, gestión de riesgos |
| Espinosa Medina Luis Layonet | Ingeniero de Requerimientos | Requerimientos + Investigación/UX (wireframes) |
| De La Cruz Ramírez Benjamín | Control de Calidad / Monitor | Estándares, revisión de entregables, plan de pruebas formal |
| Luna Luna Marcos Augusto | Ingeniero de Pruebas | Diseño y ejecución del plan de pruebas |
| Cristóbal Gómez Jorge Alejandro | Analista de Datos / Documentación Técnica | Datos de prueba (seed data), diagramas de arquitectura |

Los demás integrantes no programan — su participación es real pero en
documentación, pruebas, datos y UX, con evidencia en commits de Git.

## Calendario (hitos fijados por la materia)

- **21 de septiembre — Entrega 1** ⬅️ **ESTAMOS AQUÍ, es lo que Code
  construye ahora**
- 19 de octubre — Entrega 2: desarrollo con funcionalidades
- 23 de noviembre — Entrega 3: prácticamente concluido

## ⚠️ ALCANCE EXACTO DE LA ENTREGA 1 (lo único que se construye ahora)

**Sí construir:**
1. Modelado lógico de la base de datos (diagrama entidad-relación: tablas,
   relaciones, llaves) cubriendo los RF001-RF015 — usuarios/roles, clientes,
   membresías, pagos, rutinas, dietas, progreso corporal
2. Modelado físico (esquema real de PostgreSQL — tipos de datos, llaves
   foráneas, migraciones iniciales con Alembic)
3. Prototipo de frontend "decente pero no completo": pantallas principales
   con diseño ya trabajado (usar los principios de Leo — nada de UI
   genérica/plantilla), navegación entre pantallas, PERO SIN lógica de
   negocio conectada al backend todavía (puede usar datos mock/estáticos)
4. Estructura base del backend en arquitectura hexagonal (carpetas
   domain/application/infrastructure/api) — sin implementar todos los casos
   de uso todavía, solo el esqueleto que sostiene el modelo de datos

**NO construir todavía (eso es Entrega 2, 19 de octubre):**
- Lógica de negocio completa de los casos de uso
- Conexión real frontend↔backend
- Auth funcional (JWT) — el modelo de datos de usuarios/roles sí, pero el
  flujo de login funcionando no
- Pagos, notificaciones de vencimiento, dashboard de progreso funcionando
  de verdad

## Documentación obligatoria durante el desarrollo

Cada decisión de arquitectura que tome Isai (aprobada, rechazada, o
corregida) se registra en `DECISIONES.md` en la raíz del proyecto, con
formato: fecha, qué se propuso, decisión de Isai, por qué, alternativa
aplicada si aplica. Esto ya está integrado en el comando `/nuevo-proyecto`.

## Documentación formal de la materia (ya generada)

Ya existe `SmartGym-v2-Documentacion.docx` con Apartado I y II completos, y
Apartado III con los 15 RF (3.2 y 3.3 pendientes de diagramas — se llenan
con lo que resulte del modelado que Code construya en esta entrega).
Pendiente por completar ahí: boleta y correo de Cristóbal Gómez Jorge
Alejandro, y la liga real de Microsoft Planner.

## Equipo de agentes (subagentes de Claude Code) — ya copiados a este repo

| Agente | Rol |
|---|---|
| Isai | Arquitectura y diseño — revisa antes de construir, explica el porqué |
| Benja | Coordinador — reparte trabajo entre los demás |
| Valde | Backend — FastAPI, dominio, PostgreSQL/SQLAlchemy |
| Leo | Frontend — React/Vite/TypeScript, diseño visual distintivo (nunca genérico) |
| Ramon | Seguridad — OWASP, JWT/roles |
| Cofi | QA — pytest |
| Royer | DevOps — Docker, docker-compose |
| Bueno | Nube/AWS — para Entrega 3, no aplica todavía |

Ya están en `SmartGym-v2\.claude\agents\`. El comando `/nuevo-proyecto` ya
está creado en `dev\.claude\commands\` con la obligación de documentar en
`DECISIONES.md`.

## Cómo arrancar esta sesión

```
/nuevo-proyecto Lee SMARTGYM-V2-BRIEF.md en esta carpeta para todo el
contexto. Construye SOLO el alcance de la Entrega 1 descrito en la sección
"ALCANCE EXACTO DE LA ENTREGA 1" — no construyas nada de la Entrega 2 todavía.
```

Isai debe entrar primero a revisar el modelo de datos propuesto antes de que
Valde cree las migraciones, y antes de que Leo construya el prototipo de
frontend.

## Notas importantes para quien retome esto

- No reutilizar código del SmartGym v1 (Flask/SQL Server) — solo el
  conocimiento del dominio
- Jefe prefiere avanzar directo entre pasos sin que se le pregunte
  "¿seguimos?" repetidamente en sesiones largas
- Jefe prefiere cerrar el diseño/idea completo antes de empezar a construir
  código — avisa explícitamente cuando quiere pasar de discutir a construir
