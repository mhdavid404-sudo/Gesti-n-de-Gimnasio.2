import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { AuthUser } from '../api/authStorage'
import { apiFetch, ApiError } from '../api/client'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type { PasswordResetResponse, UserCreatePayload, UserUpdatePayload } from '../types/api'
import './UsersPage.css'

type AdminRole = 'admin' | 'entrenador'

const ROLE_LABELS: Record<AdminRole, string> = { admin: 'Admin', entrenador: 'Entrenador' }

const ROLE_FILTERS: { value: '' | AdminRole; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'admin', label: 'Admin' },
  { value: 'entrenador', label: 'Entrenador' },
]

/**
 * Pantalla "Usuarios" (2026-11-18): administración de cuentas de
 * admin/entrenador, solo admin -- mismo patrón visual y de componentes que
 * "Planes y servicios" (tabla + `ConfirmDialog` + `Toast`). Los clientes NO
 * aparecen aquí, se gestionan en "Clientes" (tienen su propio alta vía
 * `POST /clients`, con `ClientProfile` además del `User`).
 *
 * Protección de ruta: el link desaparece del menú para `entrenador`/
 * `cliente` (ver `Sidebar.tsx`), pero a diferencia de "Bitácora"
 * (`GET /audit-logs` es admin-only en el backend, así que un 403 real
 * protege la URL directa), `GET /users` SÍ está autorizado para
 * `entrenador` desde Entrega 2 (RF012: consultar info básica de otros
 * usuarios para asignar rutinas/dietas) -- cambiar esa autorización
 * compartida para blindar esta pantalla habría sido tocar un endpoint que
 * otras pantallas ya usan, fuera del alcance de esta tarea. Por eso esta
 * pantalla agrega su PROPIO chequeo de rol en el cliente (no llama a la API
 * en absoluto si `user.role !== 'admin'`) para lograr el mismo resultado
 * visible que "Bitácora" sin tocar `GET /users`. Las acciones de escritura
 * (`POST`/`PATCH /users`, `POST .../reset-password`) ya eran admin-only en
 * el backend desde antes -- ningún otro rol podría mutarlas aunque
 * burlara este chequeo del frontend.
 */
export function UsersPage() {
  const { user: currentUser, logout } = useAuth()
  const isAdmin = currentUser?.role === 'admin'

  const [roleFilter, setRoleFilter] = useState<'' | AdminRole>('')
  const [users, setUsers] = useState<AuthUser[] | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  const handleApiError = (err: unknown, onOther: (message: string) => void) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        return
      }
      if (err.status === 403) {
        onOther('No tienes permiso para administrar cuentas de usuario.')
        return
      }
      onOther(err.message)
      return
    }
    onOther('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  const loadUsers = () => {
    if (!isAdmin) return
    setIsLoading(true)
    setErrorMessage(null)
    const request =
      roleFilter === ''
        ? Promise.all([
            apiFetch<AuthUser[]>('/users?role=admin'),
            apiFetch<AuthUser[]>('/users?role=entrenador'),
          ]).then(([admins, entrenadores]) => [...admins, ...entrenadores])
        : apiFetch<AuthUser[]>(`/users?role=${roleFilter}`)

    request
      .then(setUsers)
      .catch((err: unknown) => handleApiError(err, setErrorMessage))
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    loadUsers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleFilter, isAdmin])

  // --- Alta de usuario (admin/entrenador) -----------------------------------
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createFullName, setCreateFullName] = useState('')
  const [createEmail, setCreateEmail] = useState('')
  const [createRole, setCreateRole] = useState<AdminRole>('entrenador')
  const [createPassword, setCreatePassword] = useState('')
  const [createError, setCreateError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  const resetCreateForm = () => {
    setCreateFullName('')
    setCreateEmail('')
    setCreateRole('entrenador')
    setCreatePassword('')
    setCreateError(null)
  }

  const handleCreateSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setCreateError(null)

    if (!createFullName.trim()) return setCreateError('Ingresa el nombre completo.')
    if (!createEmail.trim()) return setCreateError('Ingresa un correo.')
    if (createPassword.length < 8) return setCreateError('La contraseña inicial debe tener al menos 8 caracteres.')

    const payload: UserCreatePayload = {
      email: createEmail.trim(),
      password: createPassword,
      full_name: createFullName.trim(),
      role: createRole,
    }

    setIsCreating(true)
    try {
      const created = await apiFetch<AuthUser>('/users', { method: 'POST', body: payload })
      setUsers((prev) => (roleFilter === '' || roleFilter === created.role ? [...(prev ?? []), created] : prev))
      setToast(`Usuario "${created.full_name}" creado como ${ROLE_LABELS[created.role as AdminRole]}.`)
      setShowCreateForm(false)
      resetCreateForm()
    } catch (err) {
      handleApiError(err, setCreateError)
    } finally {
      setIsCreating(false)
    }
  }

  // --- Restablecer contraseña ------------------------------------------------
  const [userToReset, setUserToReset] = useState<AuthUser | null>(null)
  const [isResetting, setIsResetting] = useState(false)

  const handleResetPassword = async () => {
    if (!userToReset) return
    setIsResetting(true)
    try {
      const response = await apiFetch<PasswordResetResponse>(`/users/${userToReset.id}/reset-password`, {
        method: 'POST',
      })
      setToast(
        `Contraseña restablecida para "${userToReset.full_name}". Nueva contraseña temporal: ${response.temporary_password} (cópiala y compártela; no se mostrará de nuevo).`,
      )
    } catch (err) {
      handleApiError(err, setToast)
    } finally {
      setIsResetting(false)
      setUserToReset(null)
    }
  }

  // --- Activar / desactivar ----------------------------------------------
  const [togglingUserId, setTogglingUserId] = useState<number | null>(null)

  const handleToggleActive = async (target: AuthUser) => {
    setTogglingUserId(target.id)
    try {
      const payload: UserUpdatePayload = { is_active: !target.is_active }
      const updated = await apiFetch<AuthUser>(`/users/${target.id}`, { method: 'PATCH', body: payload })
      setUsers((prev) => (prev ?? []).map((u) => (u.id === updated.id ? updated : u)))
      setToast(`Usuario "${updated.full_name}" ${updated.is_active ? 'activado' : 'desactivado'} correctamente.`)
    } catch (err) {
      handleApiError(err, setToast)
    } finally {
      setTogglingUserId(null)
    }
  }

  if (!isAdmin) {
    return (
      <div className="users-page">
        <ErrorMessage message="Solo el administrador puede administrar cuentas de usuario." />
      </div>
    )
  }

  return (
    <div className="users-page">
      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}

      <div className="users-page__header">
        <h2 className="section-title">Usuarios</h2>
        <span className="eyebrow">Cuentas de administrador y entrenador -- los clientes se gestionan en "Clientes"</span>
      </div>

      <div className="users-page__toolbar">
        <div className="users-page__filter">
          <label className="field-label" htmlFor="roleFilter">
            Filtrar por rol
          </label>
          <select
            id="roleFilter"
            className="input"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as '' | AdminRole)}
          >
            {ROLE_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => {
            resetCreateForm()
            setShowCreateForm((v) => !v)
          }}
        >
          {showCreateForm ? 'Cancelar' : '+ Nuevo usuario'}
        </button>
      </div>

      {showCreateForm && (
        <form className="card users-page__inline-form" onSubmit={handleCreateSubmit}>
          {createError && <ErrorMessage title="No se pudo crear el usuario" message={createError} />}
          <div className="users-page__form-row">
            <div className="users-page__field">
              <label className="field-label" htmlFor="createFullName">
                Nombre completo
              </label>
              <input
                id="createFullName"
                className="input"
                value={createFullName}
                onChange={(e) => setCreateFullName(e.target.value)}
              />
            </div>
            <div className="users-page__field">
              <label className="field-label" htmlFor="createEmail">
                Correo
              </label>
              <input
                id="createEmail"
                type="email"
                className="input"
                value={createEmail}
                onChange={(e) => setCreateEmail(e.target.value)}
              />
            </div>
          </div>
          <div className="users-page__form-row">
            <div className="users-page__field">
              <label className="field-label" htmlFor="createRole">
                Rol
              </label>
              <select
                id="createRole"
                className="input"
                value={createRole}
                onChange={(e) => setCreateRole(e.target.value as AdminRole)}
              >
                <option value="entrenador">Entrenador</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div className="users-page__field">
              <label className="field-label" htmlFor="createPassword">
                Contraseña inicial
              </label>
              <input
                id="createPassword"
                type="text"
                className="input"
                value={createPassword}
                onChange={(e) => setCreatePassword(e.target.value)}
                placeholder="Mínimo 8 caracteres"
              />
            </div>
          </div>
          <div className="users-page__form-actions">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setShowCreateForm(false)
                resetCreateForm()
              }}
            >
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={isCreating}>
              {isCreating ? 'Creando…' : 'Crear usuario'}
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="card">
          <LoadingState label="Cargando usuarios…" variant="skeleton" rows={4} />
        </div>
      ) : errorMessage ? (
        <ErrorMessage message={errorMessage} onRetry={loadUsers} />
      ) : !users || users.length === 0 ? (
        <div className="card">
          <EmptyState title="Sin usuarios" description='Crea el primero con "+ Nuevo usuario".' />
        </div>
      ) : (
        <div className="card users-page__table-wrap">
          <table className="users-page__table data-table">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Correo</th>
                <th>Rol</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isSelf = u.id === currentUser?.id
                return (
                  <tr key={u.id}>
                    <td>
                      {u.full_name}
                      {isSelf && <span className="users-page__you-tag">(tú)</span>}
                    </td>
                    <td>{u.email}</td>
                    <td>{ROLE_LABELS[u.role as AdminRole] ?? u.role}</td>
                    <td>
                      <StatusPill status={u.is_active ? 'activa' : 'inactivo'} />
                    </td>
                    <td className="users-page__row-actions">
                      <button type="button" className="btn btn-ghost" onClick={() => setUserToReset(u)}>
                        Restablecer contraseña
                      </button>
                      {!isSelf && (
                        <button
                          type="button"
                          className="btn btn-ghost"
                          disabled={togglingUserId === u.id}
                          onClick={() => handleToggleActive(u)}
                        >
                          {togglingUserId === u.id ? 'Guardando…' : u.is_active ? 'Desactivar' : 'Activar'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={userToReset != null}
        title={`¿Restablecer la contraseña de ${userToReset?.full_name}?`}
        description="Se genera una contraseña temporal nueva y la anterior deja de funcionar de inmediato. La temporal se muestra una sola vez al confirmar -- cópiala y compártela con esa persona."
        tone="neutral"
        confirmLabel={isResetting ? 'Restableciendo…' : 'Restablecer'}
        onConfirm={handleResetPassword}
        onCancel={() => setUserToReset(null)}
      />
    </div>
  )
}
