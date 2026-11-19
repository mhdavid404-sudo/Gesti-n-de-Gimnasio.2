import { Fragment, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { apiFetch, ApiError } from '../api/client'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type {
  ApiClientProfile,
  ApiExercise,
  ApiRoutine,
  ApiRoutineAssignment,
  ApiRoutineAssignmentStatus,
  ApiRoutineExercise,
  ExerciseCreatePayload,
  RoutineAssignmentCreatePayload,
  RoutineAssignmentUpdatePayload,
  RoutineCreatePayload,
  RoutineDeleteResult,
  RoutineUpdatePayload,
  RoutineExerciseCreatePayload,
} from '../types/api'
import './RoutinesPage.css'

const todayIso = () => new Date().toISOString().slice(0, 10)

const ASSIGNMENT_STATUSES: { value: ApiRoutineAssignmentStatus; label: string }[] = [
  { value: 'activa', label: 'Activa' },
  { value: 'completada', label: 'Completada' },
  { value: 'cancelada', label: 'Cancelada' },
]

/**
 * Conectado a la API real (RF007, RF008) — ver docstring de
 * `backend/src/api/v1/routers/routines.py` para la autorización exacta de
 * cada endpoint.
 *
 * No existe un endpoint de "listar todas las asignaciones del gimnasio" (a
 * propósito, mismo criterio de ownership-por-dato que el resto del
 * proyecto) -- la sección "Asignaciones" se rediseñó respecto al mock: en
 * vez de una tabla global, se elige un cliente (`GET /clients`, ya scoped
 * por rol -- un entrenador ya solo ve ahí a sus propios clientes) y se
 * muestra/gestiona el historial de rutinas de ESE cliente
 * (`GET /routines/assignments/clients/{id}`). Para el rol `cliente` no hay
 * selector: se resuelve su propio `client_id` vía `GET /clients/me` y se
 * muestra directo su propio historial (RF013, solo lectura).
 */
export function RoutinesPage() {
  const { user, logout } = useAuth()
  const isStaff = user?.role === 'admin' || user?.role === 'entrenador'
  const isCliente = user?.role === 'cliente'

  const handleAuthError = (err: unknown, onOther: (message: string) => void, onForbidden?: () => void) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        return
      }
      if (err.status === 403 && onForbidden) {
        onForbidden()
        return
      }
      onOther(err.message)
      return
    }
    onOther('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  // --- Catálogo de ejercicios ---------------------------------------------
  const [exercises, setExercises] = useState<ApiExercise[] | null>(null)
  const [exercisesLoading, setExercisesLoading] = useState(true)
  const [exercisesError, setExercisesError] = useState<string | null>(null)

  const loadExercises = () => {
    setExercisesLoading(true)
    setExercisesError(null)
    apiFetch<ApiExercise[]>('/exercises')
      .then(setExercises)
      .catch((err: unknown) => handleAuthError(err, setExercisesError))
      .finally(() => setExercisesLoading(false))
  }

  useEffect(() => {
    loadExercises()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Alta inline de ejercicio -- mismo criterio ya usado para planes de
  // membresía en MembershipsPage.tsx (alta inline, sin sobre-construir).
  const [showExerciseForm, setShowExerciseForm] = useState(false)
  const [exerciseName, setExerciseName] = useState('')
  const [exerciseMuscleGroup, setExerciseMuscleGroup] = useState('')
  const [exerciseEquipment, setExerciseEquipment] = useState('')
  const [exerciseDescription, setExerciseDescription] = useState('')
  const [exerciseServerError, setExerciseServerError] = useState<string | null>(null)
  const [isSubmittingExercise, setIsSubmittingExercise] = useState(false)
  const [exerciseToast, setExerciseToast] = useState<string | null>(null)

  const resetExerciseForm = () => {
    setExerciseName('')
    setExerciseMuscleGroup('')
    setExerciseEquipment('')
    setExerciseDescription('')
    setExerciseServerError(null)
  }

  const handleCreateExercise = async (event: FormEvent) => {
    event.preventDefault()
    setExerciseServerError(null)

    if (!exerciseName.trim()) {
      setExerciseServerError('Ingresa el nombre del ejercicio.')
      return
    }

    const payload: ExerciseCreatePayload = {
      name: exerciseName.trim(),
      muscle_group: exerciseMuscleGroup.trim() || null,
      equipment: exerciseEquipment.trim() || null,
      description: exerciseDescription.trim() || null,
    }

    setIsSubmittingExercise(true)
    try {
      const created = await apiFetch<ApiExercise>('/exercises', { method: 'POST', body: payload })
      setExercises((prev) => [...(prev ?? []), created])
      setExerciseToast(`Ejercicio "${created.name}" agregado al catálogo.`)
      resetExerciseForm()
      setShowExerciseForm(false)
    } catch (err) {
      handleAuthError(
        err,
        setExerciseServerError,
        () => setExerciseServerError('No tienes permiso para agregar ejercicios al catálogo.'),
      )
    } finally {
      setIsSubmittingExercise(false)
    }
  }

  // --- Catálogo de rutinas -------------------------------------------------
  const [routines, setRoutines] = useState<ApiRoutine[] | null>(null)
  const [routinesLoading, setRoutinesLoading] = useState(true)
  const [routinesError, setRoutinesError] = useState<string | null>(null)

  const loadRoutines = () => {
    setRoutinesLoading(true)
    setRoutinesError(null)
    apiFetch<ApiRoutine[]>('/routines')
      .then(setRoutines)
      .catch((err: unknown) => handleAuthError(err, setRoutinesError))
      .finally(() => setRoutinesLoading(false))
  }

  useEffect(() => {
    loadRoutines()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const exerciseById = useMemo(() => {
    const map = new Map<number, ApiExercise>()
    exercises?.forEach((e) => map.set(e.id, e))
    return map
  }, [exercises])

  const routineById = useMemo(() => {
    const map = new Map<number, ApiRoutine>()
    routines?.forEach((r) => map.set(r.id, r))
    return map
  }, [routines])

  // Ejercicios de cada rutina: cargados bajo demanda al expandir el
  // <details> (evita N+1 si hay muchas rutinas, ver encargo).
  const [routineExercisesById, setRoutineExercisesById] = useState<Map<number, ApiRoutineExercise[]>>(new Map())
  const [loadingRoutineIds, setLoadingRoutineIds] = useState<Set<number>>(new Set())
  const [routineExerciseErrors, setRoutineExerciseErrors] = useState<Map<number, string>>(new Map())

  const loadRoutineExercises = (routineId: number) => {
    if (routineExercisesById.has(routineId) || loadingRoutineIds.has(routineId)) return
    setLoadingRoutineIds((prev) => new Set(prev).add(routineId))
    apiFetch<ApiRoutineExercise[]>(`/routines/${routineId}/exercises`)
      .then((items) => {
        setRoutineExercisesById((prev) => new Map(prev).set(routineId, items))
      })
      .catch((err: unknown) => {
        handleAuthError(err, (message) => {
          setRoutineExerciseErrors((prev) => new Map(prev).set(routineId, message))
        })
      })
      .finally(() => {
        setLoadingRoutineIds((prev) => {
          const next = new Set(prev)
          next.delete(routineId)
          return next
        })
      })
  }

  // Alta de rutina (admin/entrenador) ---------------------------------------
  const [showRoutineForm, setShowRoutineForm] = useState(false)
  const [routineName, setRoutineName] = useState('')
  const [routineDescription, setRoutineDescription] = useState('')
  const [routineServerError, setRoutineServerError] = useState<string | null>(null)
  const [isSubmittingRoutine, setIsSubmittingRoutine] = useState(false)
  const [routineToast, setRoutineToast] = useState<string | null>(null)

  const resetRoutineForm = () => {
    setRoutineName('')
    setRoutineDescription('')
    setRoutineServerError(null)
  }

  const handleCreateRoutine = async (event: FormEvent) => {
    event.preventDefault()
    setRoutineServerError(null)

    if (!routineName.trim()) {
      setRoutineServerError('Ingresa el nombre de la rutina.')
      return
    }

    const payload: RoutineCreatePayload = {
      name: routineName.trim(),
      description: routineDescription.trim() || null,
    }

    setIsSubmittingRoutine(true)
    try {
      const created = await apiFetch<ApiRoutine>('/routines', { method: 'POST', body: payload })
      setRoutines((prev) => [created, ...(prev ?? [])])
      setRoutineToast(`Rutina "${created.name}" creada.`)
      resetRoutineForm()
      setShowRoutineForm(false)
    } catch (err) {
      handleAuthError(
        err,
        setRoutineServerError,
        () => setRoutineServerError('No tienes permiso para crear rutinas.'),
      )
    } finally {
      setIsSubmittingRoutine(false)
    }
  }

  // Editar/eliminar rutina (admin cualquiera, entrenador solo la suya --
  // 2026-11-18, ampliación de RF012) ---------------------------------------
  const [editingRoutineId, setEditingRoutineId] = useState<number | null>(null)
  const [editRoutineName, setEditRoutineName] = useState('')
  const [editRoutineDescription, setEditRoutineDescription] = useState('')
  const [editRoutineServerError, setEditRoutineServerError] = useState<string | null>(null)
  const [isSavingRoutineEdit, setIsSavingRoutineEdit] = useState(false)

  const canManageRoutine = (routine: ApiRoutine) =>
    user?.role === 'admin' || (user?.role === 'entrenador' && routine.created_by === user.id)

  const openEditRoutineForm = (routine: ApiRoutine) => {
    setEditingRoutineId(routine.id)
    setEditRoutineName(routine.name)
    setEditRoutineDescription(routine.description ?? '')
    setEditRoutineServerError(null)
  }

  const handleEditRoutine = async (event: FormEvent, routineId: number) => {
    event.preventDefault()
    setEditRoutineServerError(null)

    if (!editRoutineName.trim()) {
      setEditRoutineServerError('Ingresa el nombre de la rutina.')
      return
    }

    const payload: RoutineUpdatePayload = {
      name: editRoutineName.trim(),
      description: editRoutineDescription.trim() || null,
    }

    setIsSavingRoutineEdit(true)
    try {
      const updated = await apiFetch<ApiRoutine>(`/routines/${routineId}`, { method: 'PATCH', body: payload })
      setRoutines((prev) => (prev ?? []).map((r) => (r.id === updated.id ? updated : r)))
      setRoutineToast(`Rutina "${updated.name}" actualizada.`)
      setEditingRoutineId(null)
    } catch (err) {
      handleAuthError(
        err,
        setEditRoutineServerError,
        () => setEditRoutineServerError('No tienes permiso para editar esta rutina.'),
      )
    } finally {
      setIsSavingRoutineEdit(false)
    }
  }

  const [deletingRoutine, setDeletingRoutine] = useState<ApiRoutine | null>(null)
  const [isDeletingRoutine, setIsDeletingRoutine] = useState(false)
  const [deleteRoutineError, setDeleteRoutineError] = useState<string | null>(null)

  const handleDeleteRoutine = async () => {
    if (!deletingRoutine) return
    setIsDeletingRoutine(true)
    try {
      const result = await apiFetch<RoutineDeleteResult>(`/routines/${deletingRoutine.id}`, { method: 'DELETE' })
      if (result.deleted) {
        setRoutines((prev) => (prev ?? []).filter((r) => r.id !== deletingRoutine.id))
      } else if (result.routine) {
        setRoutines((prev) => (prev ?? []).map((r) => (r.id === result.routine!.id ? result.routine! : r)))
      }
      setRoutineToast(result.message)
      setDeletingRoutine(null)
    } catch (err) {
      handleAuthError(
        err,
        (message) => {
          setDeleteRoutineError(message)
          setDeletingRoutine(null)
        },
        () => {
          setDeleteRoutineError('No tienes permiso para eliminar esta rutina.')
          setDeletingRoutine(null)
        },
      )
    } finally {
      setIsDeletingRoutine(false)
    }
  }

  // Agregar ejercicio a una rutina (admin/entrenador) -- un solo formulario
  // abierto a la vez, identificado por `addExerciseRoutineId`.
  const [addExerciseRoutineId, setAddExerciseRoutineId] = useState<number | null>(null)
  const [newExerciseId, setNewExerciseId] = useState('')
  const [newSets, setNewSets] = useState('')
  const [newReps, setNewReps] = useState('')
  const [newOrderIndex, setNewOrderIndex] = useState('0')
  const [newRestSeconds, setNewRestSeconds] = useState('')
  const [newNotes, setNewNotes] = useState('')
  const [addExerciseServerError, setAddExerciseServerError] = useState<string | null>(null)
  const [isAddingExercise, setIsAddingExercise] = useState(false)

  const openAddExerciseForm = (routineId: number) => {
    setAddExerciseRoutineId(routineId)
    setNewExerciseId('')
    setNewSets('')
    setNewReps('')
    setNewOrderIndex('0')
    setNewRestSeconds('')
    setNewNotes('')
    setAddExerciseServerError(null)
  }

  const handleAddExerciseToRoutine = async (event: FormEvent, routineId: number) => {
    event.preventDefault()
    setAddExerciseServerError(null)

    const setsValue = Number(newSets)
    const repsValue = Number(newReps)
    const orderValue = Number(newOrderIndex)
    if (!newExerciseId) {
      setAddExerciseServerError('Selecciona un ejercicio del catálogo.')
      return
    }
    if (!newSets || Number.isNaN(setsValue) || setsValue <= 0) {
      setAddExerciseServerError('Ingresa un número de series mayor a 0.')
      return
    }
    if (!newReps || Number.isNaN(repsValue) || repsValue <= 0) {
      setAddExerciseServerError('Ingresa un número de repeticiones mayor a 0.')
      return
    }
    if (newOrderIndex === '' || Number.isNaN(orderValue) || orderValue < 0) {
      setAddExerciseServerError('Ingresa un orden válido (0 o mayor).')
      return
    }

    const payload: RoutineExerciseCreatePayload = {
      exercise_id: Number(newExerciseId),
      sets: setsValue,
      reps: repsValue,
      order_index: orderValue,
      rest_seconds: newRestSeconds ? Number(newRestSeconds) : null,
      notes: newNotes.trim() || null,
    }

    setIsAddingExercise(true)
    try {
      const created = await apiFetch<ApiRoutineExercise>(`/routines/${routineId}/exercises`, {
        method: 'POST',
        body: payload,
      })
      setRoutineExercisesById((prev) => {
        const next = new Map(prev)
        const current = next.get(routineId) ?? []
        next.set(routineId, [...current, created].sort((a, b) => a.order_index - b.order_index))
        return next
      })
      setAddExerciseRoutineId(null)
    } catch (err) {
      handleAuthError(
        err,
        setAddExerciseServerError,
        () => setAddExerciseServerError('No tienes permiso para agregar ejercicios a esta rutina.'),
      )
    } finally {
      setIsAddingExercise(false)
    }
  }

  // --- Asignaciones ---------------------------------------------------------
  // Selector de cliente (admin/entrenador) en vez de una tabla global --
  // ver docstring de la función y DECISIONES.md.
  const [clients, setClients] = useState<ApiClientProfile[] | null>(null)
  const [clientsLoading, setClientsLoading] = useState(true)
  const [clientsError, setClientsError] = useState<string | null>(null)
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [ownClientName, setOwnClientName] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return

    if (isCliente) {
      setClientsLoading(true)
      setClientsError(null)
      apiFetch<ApiClientProfile>('/clients/me')
        .then((profile) => {
          setSelectedClientId(profile.id)
          setOwnClientName(profile.full_name)
        })
        .catch((err: unknown) => handleAuthError(err, setClientsError))
        .finally(() => setClientsLoading(false))
      return
    }

    setClientsLoading(true)
    setClientsError(null)
    apiFetch<ApiClientProfile[]>('/clients')
      .then((data) => setClients(data))
      .catch((err: unknown) =>
        handleAuthError(err, setClientsError, () => setClientsError('No tienes permiso para ver clientes.')),
      )
      .finally(() => setClientsLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.role])

  const [assignments, setAssignments] = useState<ApiRoutineAssignment[] | null>(null)
  const [assignmentsLoading, setAssignmentsLoading] = useState(false)
  const [assignmentsError, setAssignmentsError] = useState<string | null>(null)

  const loadAssignments = (clientId: number) => {
    setAssignmentsLoading(true)
    setAssignmentsError(null)
    apiFetch<ApiRoutineAssignment[]>(`/routines/assignments/clients/${clientId}`)
      .then(setAssignments)
      .catch((err: unknown) =>
        handleAuthError(err, setAssignmentsError, () => setAssignmentsError('No tienes acceso al historial de este cliente.')),
      )
      .finally(() => setAssignmentsLoading(false))
  }

  useEffect(() => {
    if (selectedClientId == null) {
      setAssignments(null)
      return
    }
    loadAssignments(selectedClientId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedClientId])

  // Alta de asignación (admin/entrenador) -----------------------------------
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [assignRoutineId, setAssignRoutineId] = useState('')
  const [assignDate, setAssignDate] = useState(todayIso)
  const [assignServerError, setAssignServerError] = useState<string | null>(null)
  const [isAssigning, setIsAssigning] = useState(false)
  const [assignToast, setAssignToast] = useState<string | null>(null)

  const resetAssignForm = () => {
    setAssignRoutineId('')
    setAssignDate(todayIso())
    setAssignServerError(null)
  }

  const handleCreateAssignment = async (event: FormEvent) => {
    event.preventDefault()
    setAssignServerError(null)
    if (selectedClientId == null) return

    if (!assignRoutineId) {
      setAssignServerError('Selecciona una rutina.')
      return
    }
    if (!assignDate) {
      setAssignServerError('Selecciona una fecha de asignación.')
      return
    }

    const payload: RoutineAssignmentCreatePayload = {
      routine_id: Number(assignRoutineId),
      client_id: selectedClientId,
      assigned_date: assignDate,
    }

    setIsAssigning(true)
    try {
      const created = await apiFetch<ApiRoutineAssignment>('/routines/assignments', { method: 'POST', body: payload })
      setAssignments((prev) => [created, ...(prev ?? [])])
      setAssignToast('Rutina asignada correctamente.')
      resetAssignForm()
      setShowAssignForm(false)
    } catch (err) {
      handleAuthError(
        err,
        setAssignServerError,
        () => setAssignServerError('No tienes permiso para asignar esta rutina a este cliente.'),
      )
    } finally {
      setIsAssigning(false)
    }
  }

  // Cambiar status de una asignación existente (admin, o entrenador dueño
  // del cliente -- ya garantizado porque solo aparece en el selector si el
  // backend lo dejó ver/listar, ver docstring de la función).
  const [updatingAssignmentId, setUpdatingAssignmentId] = useState<number | null>(null)
  const [updateError, setUpdateError] = useState<string | null>(null)

  const handleUpdateStatus = async (assignment: ApiRoutineAssignment, status: ApiRoutineAssignmentStatus) => {
    if (status === assignment.status) return
    setUpdateError(null)
    setUpdatingAssignmentId(assignment.id)
    try {
      const updated = await apiFetch<ApiRoutineAssignment>(`/routines/assignments/${assignment.id}`, {
        method: 'PATCH',
        body: { status },
      })
      setAssignments((prev) => (prev ?? []).map((a) => (a.id === updated.id ? updated : a)))
    } catch (err) {
      handleAuthError(
        err,
        setUpdateError,
        () => setUpdateError('No tienes permiso para actualizar esta asignación.'),
      )
    } finally {
      setUpdatingAssignmentId(null)
    }
  }

  // Corregir una asignación (rutina/fecha, "error de dedo") y quitarla sin
  // perder la bitácora -- 2026-11-18, ampliación de RF012.
  const [editingAssignmentId, setEditingAssignmentId] = useState<number | null>(null)
  const [editAssignRoutineId, setEditAssignRoutineId] = useState('')
  const [editAssignDate, setEditAssignDate] = useState('')
  const [editAssignServerError, setEditAssignServerError] = useState<string | null>(null)
  const [isSavingAssignEdit, setIsSavingAssignEdit] = useState(false)

  const openEditAssignmentForm = (assignment: ApiRoutineAssignment) => {
    setEditingAssignmentId(assignment.id)
    setEditAssignRoutineId(String(assignment.routine_id))
    setEditAssignDate(assignment.assigned_date)
    setEditAssignServerError(null)
  }

  const handleSaveAssignmentEdit = async (event: FormEvent, assignment: ApiRoutineAssignment) => {
    event.preventDefault()
    setEditAssignServerError(null)

    const payload: RoutineAssignmentUpdatePayload = {
      routine_id: Number(editAssignRoutineId),
      assigned_date: editAssignDate,
    }

    setIsSavingAssignEdit(true)
    try {
      const updated = await apiFetch<ApiRoutineAssignment>(`/routines/assignments/${assignment.id}`, {
        method: 'PATCH',
        body: payload,
      })
      setAssignments((prev) => (prev ?? []).map((a) => (a.id === updated.id ? updated : a)))
      setEditingAssignmentId(null)
    } catch (err) {
      handleAuthError(
        err,
        setEditAssignServerError,
        () => setEditAssignServerError('No tienes permiso para corregir esta asignación.'),
      )
    } finally {
      setIsSavingAssignEdit(false)
    }
  }

  const [deletingAssignment, setDeletingAssignment] = useState<ApiRoutineAssignment | null>(null)
  const [isDeletingAssignment, setIsDeletingAssignment] = useState(false)

  const handleDeleteAssignment = async () => {
    if (!deletingAssignment) return
    setIsDeletingAssignment(true)
    try {
      await apiFetch<void>(`/routines/assignments/${deletingAssignment.id}`, { method: 'DELETE' })
      setAssignments((prev) => (prev ?? []).filter((a) => a.id !== deletingAssignment.id))
      setAssignToast('Asignación eliminada.')
      setDeletingAssignment(null)
    } catch (err) {
      handleAuthError(
        err,
        (message) => {
          setUpdateError(message)
          setDeletingAssignment(null)
        },
        () => {
          setUpdateError('No tienes permiso para eliminar esta asignación.')
          setDeletingAssignment(null)
        },
      )
    } finally {
      setIsDeletingAssignment(false)
    }
  }

  const selectedClient = clients?.find((c) => c.id === selectedClientId)

  return (
    <div className="routines-page">
      {exerciseToast && <Toast message={exerciseToast} onDismiss={() => setExerciseToast(null)} />}
      {routineToast && <Toast message={routineToast} onDismiss={() => setRoutineToast(null)} />}
      {assignToast && <Toast message={assignToast} onDismiss={() => setAssignToast(null)} />}
      {updateError && <Toast message={updateError} tone="danger" onDismiss={() => setUpdateError(null)} />}
      {deleteRoutineError && (
        <Toast message={deleteRoutineError} tone="danger" onDismiss={() => setDeleteRoutineError(null)} />
      )}

      <section>
        <div className="routines-page__section-header">
          <h2 className="section-title">Catálogo de rutinas</h2>
          <span className="eyebrow">
            {exercisesLoading ? '…' : exercises ? `${exercises.length} ejercicios en catálogo` : '0 ejercicios en catálogo'}
          </span>
        </div>

        {exercisesError && <ErrorMessage message={exercisesError} onRetry={loadExercises} />}

        {isStaff && (
          <div className="routines-page__toolbar">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setShowExerciseForm((prev) => !prev)
                if (showExerciseForm) resetExerciseForm()
              }}
            >
              {showExerciseForm ? 'Cancelar' : '+ Nuevo ejercicio'}
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                setShowRoutineForm((prev) => !prev)
                if (showRoutineForm) resetRoutineForm()
              }}
            >
              {showRoutineForm ? 'Cancelar' : '+ Nueva rutina'}
            </button>
          </div>
        )}

        {isStaff && showExerciseForm && (
          <form className="card routines-page__inline-form" onSubmit={handleCreateExercise}>
            {exerciseServerError && (
              <ErrorMessage title="No se pudo agregar el ejercicio" message={exerciseServerError} />
            )}
            <div className="routines-page__form-row">
              <div className="routines-page__field">
                <label className="field-label" htmlFor="exerciseName">
                  Nombre
                </label>
                <input
                  id="exerciseName"
                  className="input"
                  value={exerciseName}
                  onChange={(e) => setExerciseName(e.target.value)}
                  placeholder="Ej. Sentadilla"
                />
              </div>
              <div className="routines-page__field">
                <label className="field-label" htmlFor="exerciseMuscleGroup">
                  Grupo muscular
                </label>
                <input
                  id="exerciseMuscleGroup"
                  className="input"
                  value={exerciseMuscleGroup}
                  onChange={(e) => setExerciseMuscleGroup(e.target.value)}
                  placeholder="Ej. Piernas"
                />
              </div>
              <div className="routines-page__field">
                <label className="field-label" htmlFor="exerciseEquipment">
                  Equipo
                </label>
                <input
                  id="exerciseEquipment"
                  className="input"
                  value={exerciseEquipment}
                  onChange={(e) => setExerciseEquipment(e.target.value)}
                  placeholder="Ej. Barra"
                />
              </div>
            </div>
            <div className="routines-page__field">
              <label className="field-label" htmlFor="exerciseDescription">
                Descripción (opcional)
              </label>
              <input
                id="exerciseDescription"
                className="input"
                value={exerciseDescription}
                onChange={(e) => setExerciseDescription(e.target.value)}
                placeholder="Ej. Técnica, profundidad, cadencia…"
              />
            </div>
            <div className="routines-page__form-actions">
              <button type="submit" className="btn btn-primary" disabled={isSubmittingExercise}>
                {isSubmittingExercise ? 'Agregando…' : 'Agregar ejercicio'}
              </button>
            </div>
          </form>
        )}

        {isStaff && showRoutineForm && (
          <form className="card routines-page__inline-form" onSubmit={handleCreateRoutine}>
            {routineServerError && <ErrorMessage title="No se pudo crear la rutina" message={routineServerError} />}
            <div className="routines-page__field">
              <label className="field-label" htmlFor="routineName">
                Nombre
              </label>
              <input
                id="routineName"
                className="input"
                value={routineName}
                onChange={(e) => setRoutineName(e.target.value)}
                placeholder="Ej. Fuerza - Tren superior"
              />
            </div>
            <div className="routines-page__field">
              <label className="field-label" htmlFor="routineDescription">
                Descripción (opcional)
              </label>
              <input
                id="routineDescription"
                className="input"
                value={routineDescription}
                onChange={(e) => setRoutineDescription(e.target.value)}
                placeholder="Ej. 3 días por semana, enfoque en hipertrofia"
              />
            </div>
            <div className="routines-page__form-actions">
              <button type="submit" className="btn btn-primary" disabled={isSubmittingRoutine}>
                {isSubmittingRoutine ? 'Creando…' : 'Crear rutina'}
              </button>
            </div>
          </form>
        )}

        {routinesLoading ? (
          <div className="card">
            <LoadingState label="Cargando rutinas…" variant="skeleton" rows={3} />
          </div>
        ) : routinesError ? (
          <ErrorMessage message={routinesError} onRetry={loadRoutines} />
        ) : !routines || routines.length === 0 ? (
          <div className="card">
            <EmptyState
              title="Todavía no hay rutinas en el catálogo"
              description={
                isStaff
                  ? 'Crea la primera rutina con el botón "+ Nueva rutina" para empezar a asignarla a tus clientes.'
                  : 'Todavía no se ha dado de alta ninguna rutina.'
              }
            />
          </div>
        ) : (
          <div className="routines-page__catalog">
            {routines.map((routine) => {
              const items = routineExercisesById.get(routine.id)
              const isLoadingItems = loadingRoutineIds.has(routine.id)
              const itemsError = routineExerciseErrors.get(routine.id)
              return (
                <details
                  key={routine.id}
                  className="card routine-card"
                  onToggle={(e) => {
                    if ((e.target as HTMLDetailsElement).open) loadRoutineExercises(routine.id)
                  }}
                >
                  <summary>
                    <span className="routine-card__name">
                      {routine.name}
                      {!routine.is_active && <StatusPill status="inactivo" />}
                    </span>
                    <span className="routine-card__count">{items ? `${items.length} ejercicios` : 'Ver ejercicios'}</span>
                  </summary>
                  {routine.description && <p className="routine-card__description">{routine.description}</p>}

                  {canManageRoutine(routine) && editingRoutineId !== routine.id && (
                    <div className="routines-page__form-actions">
                      <button type="button" className="btn btn-ghost" onClick={() => openEditRoutineForm(routine)}>
                        Editar
                      </button>
                      <button type="button" className="btn btn-ghost" onClick={() => setDeletingRoutine(routine)}>
                        Eliminar
                      </button>
                    </div>
                  )}

                  {canManageRoutine(routine) && editingRoutineId === routine.id && (
                    <form
                      className="routines-page__inline-form routines-page__inline-form--nested"
                      onSubmit={(e) => handleEditRoutine(e, routine.id)}
                    >
                      {editRoutineServerError && (
                        <ErrorMessage title="No se pudo editar la rutina" message={editRoutineServerError} />
                      )}
                      <div className="routines-page__field">
                        <label className="field-label" htmlFor={`editRoutineName-${routine.id}`}>
                          Nombre
                        </label>
                        <input
                          id={`editRoutineName-${routine.id}`}
                          className="input"
                          value={editRoutineName}
                          onChange={(e) => setEditRoutineName(e.target.value)}
                        />
                      </div>
                      <div className="routines-page__field">
                        <label className="field-label" htmlFor={`editRoutineDescription-${routine.id}`}>
                          Descripción (opcional)
                        </label>
                        <input
                          id={`editRoutineDescription-${routine.id}`}
                          className="input"
                          value={editRoutineDescription}
                          onChange={(e) => setEditRoutineDescription(e.target.value)}
                        />
                      </div>
                      <div className="routines-page__form-actions">
                        <button type="button" className="btn btn-ghost" onClick={() => setEditingRoutineId(null)}>
                          Cancelar
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={isSavingRoutineEdit}>
                          {isSavingRoutineEdit ? 'Guardando…' : 'Guardar cambios'}
                        </button>
                      </div>
                    </form>
                  )}

                  {isLoadingItems ? (
                    <LoadingState label="Cargando ejercicios…" variant="skeleton" rows={2} />
                  ) : itemsError ? (
                    <ErrorMessage message={itemsError} onRetry={() => loadRoutineExercises(routine.id)} />
                  ) : items && items.length === 0 ? (
                    <p className="routines-page__note">Esta rutina todavía no tiene ejercicios.</p>
                  ) : items ? (
                    <table className="routines-page__table">
                      <thead>
                        <tr>
                          <th>Ejercicio</th>
                          <th>Grupo muscular</th>
                          <th>Series</th>
                          <th>Reps</th>
                          <th>Descanso</th>
                          <th>Notas</th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((it) => {
                          const exercise = exerciseById.get(it.exercise_id)
                          return (
                            <tr key={it.id}>
                              <td>{exercise?.name ?? `#${it.exercise_id}`}</td>
                              <td>{exercise?.muscle_group ?? '—'}</td>
                              <td>{it.sets}</td>
                              <td>{it.reps}</td>
                              <td>{it.rest_seconds != null ? `${it.rest_seconds}s` : '—'}</td>
                              <td>{it.notes ?? '—'}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  ) : null}

                  {isStaff && (
                    <div className="routines-page__add-exercise">
                      {addExerciseRoutineId === routine.id ? (
                        <form
                          className="routines-page__inline-form routines-page__inline-form--nested"
                          onSubmit={(e) => handleAddExerciseToRoutine(e, routine.id)}
                        >
                          {addExerciseServerError && (
                            <ErrorMessage title="No se pudo agregar el ejercicio" message={addExerciseServerError} />
                          )}
                          {!exercises || exercises.length === 0 ? (
                            <p className="routines-page__note">
                              No hay ejercicios en el catálogo -- agrega uno primero con "+ Nuevo ejercicio".
                            </p>
                          ) : (
                            <>
                              <div className="routines-page__form-row">
                                <div className="routines-page__field">
                                  <label className="field-label" htmlFor={`newExercise-${routine.id}`}>
                                    Ejercicio
                                  </label>
                                  <select
                                    id={`newExercise-${routine.id}`}
                                    className="input"
                                    value={newExerciseId}
                                    onChange={(e) => setNewExerciseId(e.target.value)}
                                  >
                                    <option value="">Selecciona un ejercicio</option>
                                    {exercises.map((ex) => (
                                      <option key={ex.id} value={ex.id}>
                                        {ex.name}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                                <div className="routines-page__field">
                                  <label className="field-label" htmlFor={`newSets-${routine.id}`}>
                                    Series
                                  </label>
                                  <input
                                    id={`newSets-${routine.id}`}
                                    type="number"
                                    min={1}
                                    className="input"
                                    value={newSets}
                                    onChange={(e) => setNewSets(e.target.value)}
                                    placeholder="4"
                                  />
                                </div>
                                <div className="routines-page__field">
                                  <label className="field-label" htmlFor={`newReps-${routine.id}`}>
                                    Reps
                                  </label>
                                  <input
                                    id={`newReps-${routine.id}`}
                                    type="number"
                                    min={1}
                                    className="input"
                                    value={newReps}
                                    onChange={(e) => setNewReps(e.target.value)}
                                    placeholder="12"
                                  />
                                </div>
                              </div>
                              <div className="routines-page__form-row">
                                <div className="routines-page__field">
                                  <label className="field-label" htmlFor={`newOrder-${routine.id}`}>
                                    Orden
                                  </label>
                                  <input
                                    id={`newOrder-${routine.id}`}
                                    type="number"
                                    min={0}
                                    className="input"
                                    value={newOrderIndex}
                                    onChange={(e) => setNewOrderIndex(e.target.value)}
                                  />
                                </div>
                                <div className="routines-page__field">
                                  <label className="field-label" htmlFor={`newRest-${routine.id}`}>
                                    Descanso (segundos, opcional)
                                  </label>
                                  <input
                                    id={`newRest-${routine.id}`}
                                    type="number"
                                    min={0}
                                    className="input"
                                    value={newRestSeconds}
                                    onChange={(e) => setNewRestSeconds(e.target.value)}
                                    placeholder="60"
                                  />
                                </div>
                                <div className="routines-page__field">
                                  <label className="field-label" htmlFor={`newNotes-${routine.id}`}>
                                    Notas (opcional)
                                  </label>
                                  <input
                                    id={`newNotes-${routine.id}`}
                                    className="input"
                                    value={newNotes}
                                    onChange={(e) => setNewNotes(e.target.value)}
                                    placeholder="Ej. al fallo"
                                  />
                                </div>
                              </div>
                              <div className="routines-page__form-actions">
                                <button type="submit" className="btn btn-primary" disabled={isAddingExercise}>
                                  {isAddingExercise ? 'Agregando…' : 'Agregar a la rutina'}
                                </button>
                              </div>
                            </>
                          )}
                          <div className="routines-page__form-actions">
                            <button
                              type="button"
                              className="btn btn-ghost"
                              onClick={() => setAddExerciseRoutineId(null)}
                            >
                              Cerrar
                            </button>
                          </div>
                        </form>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => openAddExerciseForm(routine.id)}
                        >
                          + Agregar ejercicio
                        </button>
                      )}
                    </div>
                  )}
                </details>
              )
            })}
          </div>
        )}
      </section>

      <section className="routines-page__assign-section">
        <div className="routines-page__section-header">
          <h2 className="section-title">Asignaciones</h2>
        </div>

        {clientsLoading ? (
          <div className="card">
            <LoadingState label="Cargando clientes…" variant="skeleton" rows={2} />
          </div>
        ) : clientsError ? (
          <ErrorMessage message={clientsError} />
        ) : isCliente ? (
          <p className="eyebrow routines-page__own-client">{ownClientName ?? 'Tu historial de rutinas'}</p>
        ) : (
          <div className="card routines-page__client-picker">
            <label className="field-label" htmlFor="assign-client-select">
              Cliente
            </label>
            <select
              id="assign-client-select"
              className="input"
              value={selectedClientId ?? ''}
              onChange={(e) => setSelectedClientId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">Selecciona un cliente</option>
              {clients?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedClientId == null ? (
          <div className="card">
            <EmptyState
              title="Selecciona un cliente"
              description="Elige un cliente arriba para ver y gestionar su historial de rutinas asignadas."
            />
          </div>
        ) : (
          <>
            {isStaff && (
              <div className="routines-page__toolbar">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    setShowAssignForm((prev) => !prev)
                    if (showAssignForm) resetAssignForm()
                  }}
                  disabled={!routines || routines.length === 0}
                >
                  {showAssignForm ? 'Cancelar' : '+ Asignar rutina'}
                </button>
              </div>
            )}

            {isStaff && showAssignForm && (
              <form className="card routines-page__inline-form" onSubmit={handleCreateAssignment}>
                {assignServerError && (
                  <ErrorMessage title="No se pudo asignar la rutina" message={assignServerError} />
                )}
                <div className="routines-page__form-row">
                  <div className="routines-page__field">
                    <label className="field-label" htmlFor="assignRoutineSelect">
                      Rutina
                    </label>
                    <select
                      id="assignRoutineSelect"
                      className="input"
                      value={assignRoutineId}
                      onChange={(e) => setAssignRoutineId(e.target.value)}
                    >
                      <option value="">Selecciona una rutina</option>
                      {routines?.filter((r) => r.is_active).map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="routines-page__field">
                    <label className="field-label" htmlFor="assignDateInput">
                      Fecha de asignación
                    </label>
                    <input
                      id="assignDateInput"
                      type="date"
                      className="input"
                      value={assignDate}
                      onChange={(e) => setAssignDate(e.target.value)}
                    />
                  </div>
                </div>
                <div className="routines-page__form-actions">
                  <button type="submit" className="btn btn-primary" disabled={isAssigning}>
                    {isAssigning ? 'Asignando…' : 'Asignar rutina'}
                  </button>
                </div>
              </form>
            )}

            {assignmentsLoading ? (
              <div className="card">
                <LoadingState label="Cargando historial…" variant="skeleton" rows={4} />
              </div>
            ) : assignmentsError ? (
              <ErrorMessage message={assignmentsError} onRetry={() => loadAssignments(selectedClientId)} />
            ) : !assignments || assignments.length === 0 ? (
              <div className="card">
                <EmptyState
                  title="Sin rutinas asignadas"
                  description={
                    isStaff
                      ? `${selectedClient?.full_name ?? 'Este cliente'} todavía no tiene rutinas asignadas.`
                      : 'Todavía no tienes rutinas asignadas.'
                  }
                />
              </div>
            ) : (
              <div className="card routines-page__table-wrap">
                <table className="routines-page__table">
                  <thead>
                    <tr>
                      <th>Rutina</th>
                      <th>Asignada</th>
                      <th>Notas</th>
                      <th>Estado</th>
                      {isStaff && <th>Acciones</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((ra) => (
                      <Fragment key={ra.id}>
                        <tr>
                          <td>{routineById.get(ra.routine_id)?.name ?? `#${ra.routine_id}`}</td>
                          <td>{ra.assigned_date}</td>
                          <td>{ra.notes ?? '—'}</td>
                          <td>
                            {isStaff ? (
                              <select
                                className="input routines-page__status-select"
                                value={ra.status}
                                disabled={updatingAssignmentId === ra.id}
                                onChange={(e) => handleUpdateStatus(ra, e.target.value as ApiRoutineAssignmentStatus)}
                              >
                                {ASSIGNMENT_STATUSES.map((s) => (
                                  <option key={s.value} value={s.value}>
                                    {s.label}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <StatusPill status={ra.status} />
                            )}
                          </td>
                          {isStaff && (
                            <td>
                              <button type="button" className="btn btn-ghost" onClick={() => openEditAssignmentForm(ra)}>
                                Corregir
                              </button>
                              <button type="button" className="btn btn-ghost" onClick={() => setDeletingAssignment(ra)}>
                                Eliminar
                              </button>
                            </td>
                          )}
                        </tr>
                        {isStaff && editingAssignmentId === ra.id && (
                          <tr>
                            <td colSpan={5}>
                              <form
                                className="routines-page__inline-form routines-page__inline-form--nested"
                                onSubmit={(e) => handleSaveAssignmentEdit(e, ra)}
                              >
                                {editAssignServerError && (
                                  <ErrorMessage title="No se pudo corregir la asignación" message={editAssignServerError} />
                                )}
                                <div className="routines-page__form-row">
                                  <div className="routines-page__field">
                                    <label className="field-label" htmlFor={`editAssignRoutine-${ra.id}`}>
                                      Rutina
                                    </label>
                                    <select
                                      id={`editAssignRoutine-${ra.id}`}
                                      className="input"
                                      value={editAssignRoutineId}
                                      onChange={(e) => setEditAssignRoutineId(e.target.value)}
                                    >
                                      {routines?.map((r) => (
                                        <option key={r.id} value={r.id}>
                                          {r.name}
                                        </option>
                                      ))}
                                    </select>
                                  </div>
                                  <div className="routines-page__field">
                                    <label className="field-label" htmlFor={`editAssignDate-${ra.id}`}>
                                      Fecha de asignación
                                    </label>
                                    <input
                                      id={`editAssignDate-${ra.id}`}
                                      type="date"
                                      className="input"
                                      value={editAssignDate}
                                      onChange={(e) => setEditAssignDate(e.target.value)}
                                    />
                                  </div>
                                </div>
                                <div className="routines-page__form-actions">
                                  <button type="button" className="btn btn-ghost" onClick={() => setEditingAssignmentId(null)}>
                                    Cancelar
                                  </button>
                                  <button type="submit" className="btn btn-primary" disabled={isSavingAssignEdit}>
                                    {isSavingAssignEdit ? 'Guardando…' : 'Guardar corrección'}
                                  </button>
                                </div>
                              </form>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>

      <ConfirmDialog
        open={deletingRoutine != null}
        title={`¿Eliminar "${deletingRoutine?.name}"?`}
        description="Si tiene asignaciones existentes, se desactivará en vez de eliminarse (se conserva el historial)."
        onConfirm={handleDeleteRoutine}
        onCancel={() => setDeletingRoutine(null)}
        confirmDisabled={isDeletingRoutine}
      />

      <ConfirmDialog
        open={deletingAssignment != null}
        title="¿Quitar esta asignación?"
        description="La asignación se eliminará del historial. La acción queda registrada en la bitácora."
        onConfirm={handleDeleteAssignment}
        onCancel={() => setDeletingAssignment(null)}
        confirmDisabled={isDeletingAssignment}
      />
    </div>
  )
}
