import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useAuth } from '../hooks/useAuth'
import type { AuthUser } from '../api/authStorage'
import type {
  ApiMembership,
  ApiMembershipPlan,
  ApiPayment,
  ApiPaymentMethod,
  ClientRegisterPayload,
  ClientRegisterResponse,
  MembershipCreatePayload,
  PaymentCreatePayload,
} from '../types/api'
import { addDaysIso } from '../utils/membership'
import './ClientFormPage.css'

const PAYMENT_METHODS: { value: ApiPaymentMethod; label: string }[] = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'tarjeta', label: 'Tarjeta' },
  { value: 'transferencia', label: 'Transferencia' },
]

const todayIso = () => new Date().toISOString().slice(0, 10)

type FormField = 'fullName' | 'email' | 'phone' | 'birthDate' | 'address' | 'amount'
type FormErrors = Partial<Record<FormField, string>>

/**
 * Alta de cliente -- ciclo completo conectado a la API real (DECISIONES.md,
 * módulo Pagos / cierre del flujo de alta, Entrega 2):
 *
 *   1. `POST /clients` -- crea `User` + `ClientProfile`, devuelve el `id` del
 *      cliente y una password temporal (ver docstring de más abajo).
 *   2. Si el admin eligió un plan: `POST /memberships` (`client_id` del paso
 *      1, `plan_id` elegido, `end_date` calculada con `duration_days`).
 *   3. Si el paso 2 tuvo éxito: `POST /payments` con los datos ya capturados
 *      en "Membresía y pago inicial".
 *
 * Criterio para "sin plan": el selector de plan incluye una opción explícita
 * "Sin membresía por ahora", preseleccionada por default -- el alta de
 * membresía/pago inicial es opcional, no se fuerza un plan por defecto. Si el
 * admin la deja así, el cliente se registra solo (sin membresía ni pago) y
 * puede asignársele una después desde su detalle.
 *
 * Manejo de fallos parciales: el paso 1, si tiene éxito, NO se revierte si
 * fallan los pasos 2/3 (el cliente ya quedó creado en el sistema). El aviso
 * de éxito/error es honesto sobre qué se completó realmente -- ver
 * `handleSubmit` más abajo y DECISIONES.md.
 *
 * Password del cliente nuevo (DECISIONES.md): el formulario no pide
 * password -- el backend genera una temporal (`RegisterClientUseCase`) y
 * la devuelve una sola vez en la respuesta; se muestra aquí en el aviso de
 * éxito para que el staff la copie y la comparta con el cliente.
 */
export function ClientFormPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  // --- Datos del cliente (conectado a POST /clients real) ---
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [address, setAddress] = useState('')
  const [emergencyContact, setEmergencyContact] = useState('')
  const [trainerId, setTrainerId] = useState('')

  const [trainers, setTrainers] = useState<AuthUser[]>([])
  const [trainersError, setTrainersError] = useState<string | null>(null)

  // --- Membresía y pago inicial (conectado a POST /memberships + POST /payments) ---
  // `planId === null` representa la opción explícita "Sin membresía por
  // ahora" -- ver docstring de arriba.
  const [plans, setPlans] = useState<ApiMembershipPlan[]>([])
  const [plansLoading, setPlansLoading] = useState(true)
  const [plansError, setPlansError] = useState<string | null>(null)
  const [planId, setPlanId] = useState<number | null>(null)
  const [paymentMethod, setPaymentMethod] = useState<ApiPaymentMethod>('efectivo')
  const [amount, setAmount] = useState('')
  const [paymentDate, setPaymentDate] = useState(todayIso)

  const [errors, setErrors] = useState<FormErrors>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const selectedPlan = useMemo(() => plans.find((p) => p.id === planId), [plans, planId])

  useEffect(() => {
    apiFetch<AuthUser[]>('/users?role=entrenador')
      .then(setTrainers)
      .catch(() => setTrainersError('No se pudo cargar la lista de entrenadores.'))
  }, [])

  useEffect(() => {
    apiFetch<ApiMembershipPlan[]>('/membership-plans')
      .then(setPlans)
      .catch(() => setPlansError('No se pudo cargar el catálogo de planes.'))
      .finally(() => setPlansLoading(false))
  }, [])

  // Limpia el error de UN campo en cuanto el usuario vuelve a escribir en
  // él — es la señal de "la interfaz escuchó" (en vez de obligar a
  // re-enviar el formulario para ver si ya quedó bien).
  const clearError = (field: FormField) => {
    setErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev))
  }

  const handlePlanChange = (id: number | null) => {
    setPlanId(id)
    clearError('amount')
    if (id === null) {
      setAmount('')
      return
    }
    const plan = plans.find((p) => p.id === id)
    if (plan) setAmount(plan.price)
  }

  const validate = (): FormErrors => {
    const next: FormErrors = {}
    if (!fullName.trim()) next.fullName = 'Ingresa el nombre completo.'
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) next.email = 'Ingresa un correo válido.'
    if (phone.replace(/\D/g, '').length < 10) next.phone = 'El teléfono debe tener al menos 10 dígitos.'
    if (!birthDate) next.birthDate = 'Selecciona una fecha de nacimiento.'
    if (!address.trim()) next.address = 'Ingresa una dirección.'
    if (planId !== null) {
      const amountValue = Number(amount)
      if (!amount || Number.isNaN(amountValue) || amountValue <= 0) {
        next.amount = 'Ingresa un monto mayor a 0.'
      }
    }
    return next
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setServerError(null)

    const nextErrors = validate()
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      return
    }

    const payload: ClientRegisterPayload = {
      email: email.trim(),
      full_name: fullName.trim(),
      trainer_id: trainerId ? Number(trainerId) : null,
      phone: phone.trim(),
      birth_date: birthDate,
      address: address.trim(),
      emergency_contact: emergencyContact.trim() || null,
    }

    const apiErrorText = (err: unknown): string =>
      err instanceof ApiError ? err.message : 'ocurrió un error inesperado.'

    setIsSubmitting(true)
    try {
      const response = await apiFetch<ClientRegisterResponse>('/clients', {
        method: 'POST',
        body: payload,
      })

      // El cliente (paso 1) YA quedó creado en este punto -- lo que sigue
      // (pasos 2/3, membresía + pago inicial) no se deshace del lado del
      // frontend si falla; el mensaje final es honesto sobre qué se
      // completó realmente (ver docstring de arriba y DECISIONES.md).
      let toastMessage = `Cliente "${response.client.full_name}" registrado. Contraseña temporal para su primer inicio de sesión: ${response.temporary_password} (cópiala y compártela con el cliente; no se mostrará de nuevo).`

      if (planId !== null && selectedPlan) {
        try {
          const membershipPayload: MembershipCreatePayload = {
            client_id: response.client.id,
            plan_id: selectedPlan.id,
            start_date: paymentDate,
            end_date: addDaysIso(paymentDate, selectedPlan.duration_days),
            status: 'activa',
          }
          const createdMembership = await apiFetch<ApiMembership>('/memberships', {
            method: 'POST',
            body: membershipPayload,
          })

          try {
            const paymentPayload: PaymentCreatePayload = {
              membership_id: createdMembership.id,
              amount: Number(amount),
              payment_date: paymentDate,
              method: paymentMethod,
            }
            await apiFetch<ApiPayment>('/payments', { method: 'POST', body: paymentPayload })
            toastMessage += ` Membresía "${selectedPlan.name}" asignada y pago de $${Number(amount).toLocaleString('es-MX')} registrado.`
          } catch (paymentErr) {
            toastMessage += ` Membresía "${selectedPlan.name}" asignada correctamente. No se pudo registrar el pago inicial: ${apiErrorText(paymentErr)} Puedes registrarlo desde la pestaña "Pagos" del detalle del cliente.`
          }
        } catch (membershipErr) {
          toastMessage += ` No se pudo asignar la membresía: ${apiErrorText(membershipErr)} Puedes asignarla y registrar el pago desde el detalle del cliente.`
        }
      }

      navigate('/clientes', { state: { toast: toastMessage } })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 409) {
          setErrors((prev) => ({ ...prev, email: err.message }))
          return
        }
        if (err.status === 403) {
          setServerError('No tienes permiso para registrar clientes.')
          return
        }
        setServerError(err.message)
        return
      }
      setServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="client-form" onSubmit={handleSubmit}>
      {serverError && <ErrorMessage title="No se pudo registrar el cliente" message={serverError} />}

      <div className="client-form__grid">
        <section className="card client-form__section">
          <h2 className="section-title">Datos del cliente</h2>
          <p className="client-form__hint">Información personal y de contacto (RF003).</p>

          <div className="client-form__field">
            <label className="field-label" htmlFor="fullName">
              Nombre completo
            </label>
            <input
              id="fullName"
              className="input"
              value={fullName}
              onChange={(e) => {
                setFullName(e.target.value)
                clearError('fullName')
              }}
              placeholder="Ej. Karla Jiménez"
              data-invalid={Boolean(errors.fullName)}
              aria-invalid={Boolean(errors.fullName)}
              aria-describedby={errors.fullName ? 'fullName-error' : undefined}
            />
            {errors.fullName && (
              <p className="field-error" id="fullName-error" role="alert">
                {errors.fullName}
              </p>
            )}
          </div>

          <div className="client-form__row">
            <div className="client-form__field">
              <label className="field-label" htmlFor="email">
                Correo
              </label>
              <input
                id="email"
                type="email"
                className="input"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  clearError('email')
                }}
                placeholder="cliente@correo.com"
                data-invalid={Boolean(errors.email)}
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && (
                <p className="field-error" id="email-error" role="alert">
                  {errors.email}
                </p>
              )}
            </div>
            <div className="client-form__field">
              <label className="field-label" htmlFor="phone">
                Teléfono
              </label>
              <input
                id="phone"
                type="tel"
                className="input"
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value)
                  clearError('phone')
                }}
                placeholder="55 1234 5678"
                data-invalid={Boolean(errors.phone)}
                aria-invalid={Boolean(errors.phone)}
                aria-describedby={errors.phone ? 'phone-error' : undefined}
              />
              {errors.phone && (
                <p className="field-error" id="phone-error" role="alert">
                  {errors.phone}
                </p>
              )}
            </div>
          </div>

          <div className="client-form__row">
            <div className="client-form__field">
              <label className="field-label" htmlFor="birthDate">
                Fecha de nacimiento
              </label>
              <input
                id="birthDate"
                type="date"
                className="input"
                value={birthDate}
                onChange={(e) => {
                  setBirthDate(e.target.value)
                  clearError('birthDate')
                }}
                data-invalid={Boolean(errors.birthDate)}
                aria-invalid={Boolean(errors.birthDate)}
                aria-describedby={errors.birthDate ? 'birthDate-error' : undefined}
              />
              {errors.birthDate && (
                <p className="field-error" id="birthDate-error" role="alert">
                  {errors.birthDate}
                </p>
              )}
            </div>
            <div className="client-form__field">
              <label className="field-label" htmlFor="trainer">
                Entrenador asignado
              </label>
              <select id="trainer" className="input" value={trainerId} onChange={(e) => setTrainerId(e.target.value)}>
                <option value="">Sin asignar</option>
                {trainers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name}
                  </option>
                ))}
              </select>
              {trainersError && <p className="client-form__hint">{trainersError}</p>}
            </div>
          </div>

          <div className="client-form__field">
            <label className="field-label" htmlFor="address">
              Dirección
            </label>
            <input
              id="address"
              className="input"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value)
                clearError('address')
              }}
              placeholder="Calle, número, colonia"
              data-invalid={Boolean(errors.address)}
              aria-invalid={Boolean(errors.address)}
              aria-describedby={errors.address ? 'address-error' : undefined}
            />
            {errors.address && (
              <p className="field-error" id="address-error" role="alert">
                {errors.address}
              </p>
            )}
          </div>

          <div className="client-form__field">
            <label className="field-label" htmlFor="emergencyContact">
              Contacto de emergencia
            </label>
            <input
              id="emergencyContact"
              className="input"
              value={emergencyContact}
              onChange={(e) => setEmergencyContact(e.target.value)}
              placeholder="Nombre y teléfono"
            />
          </div>
        </section>

        <section className="card client-form__section">
          <h2 className="section-title">Membresía y pago inicial</h2>
          <p className="client-form__hint">
            Alta de membresía y registro del primer pago (RF004 / RF005) — opcional. Si no eliges un
            plan, el cliente se registra sin membresía; puedes asignarle una después desde su detalle.
          </p>

          {plansError && <p className="client-form__hint">{plansError}</p>}

          <div className="client-form__field">
            <span className="field-label">Plan</span>
            <div className="client-form__plans" role="radiogroup" aria-label="Plan de membresía">
              <label className="client-form__plan" data-selected={planId === null}>
                <input type="radio" name="plan" checked={planId === null} onChange={() => handlePlanChange(null)} />
                <span className="client-form__plan-name">Sin membresía por ahora</span>
                <span className="client-form__plan-price">Asignar después</span>
              </label>
              {plansLoading ? (
                <p className="client-form__hint">Cargando planes…</p>
              ) : (
                plans.map((plan) => (
                  <label key={plan.id} className="client-form__plan" data-selected={plan.id === planId}>
                    <input
                      type="radio"
                      name="plan"
                      checked={plan.id === planId}
                      onChange={() => handlePlanChange(plan.id)}
                    />
                    <span className="client-form__plan-name">{plan.name}</span>
                    <span className="client-form__plan-price">${Number(plan.price).toLocaleString('es-MX')}/mes</span>
                  </label>
                ))
              )}
            </div>
          </div>

          {planId !== null && (
            <>
              <div className="client-form__row">
                <div className="client-form__field">
                  <label className="field-label" htmlFor="paymentMethod">
                    Método de pago
                  </label>
                  <select
                    id="paymentMethod"
                    className="input"
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value as ApiPaymentMethod)}
                  >
                    {PAYMENT_METHODS.map((m) => (
                      <option key={m.value} value={m.value}>
                        {m.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="client-form__field">
                  <label className="field-label" htmlFor="amount">
                    Monto
                  </label>
                  <input
                    id="amount"
                    type="number"
                    min={0}
                    step="0.01"
                    className="input"
                    value={amount}
                    onChange={(e) => {
                      setAmount(e.target.value)
                      clearError('amount')
                    }}
                    data-invalid={Boolean(errors.amount)}
                    aria-invalid={Boolean(errors.amount)}
                    aria-describedby={errors.amount ? 'amount-error' : undefined}
                  />
                  {errors.amount && (
                    <p className="field-error" id="amount-error" role="alert">
                      {errors.amount}
                    </p>
                  )}
                </div>
              </div>

              <div className="client-form__field">
                <label className="field-label" htmlFor="paymentDate">
                  Fecha de pago
                </label>
                <input
                  id="paymentDate"
                  type="date"
                  className="input"
                  value={paymentDate}
                  onChange={(e) => setPaymentDate(e.target.value)}
                  required
                />
              </div>

              {selectedPlan && (
                <div className="client-form__benefits-block">
                  <span className="field-label">Beneficios incluidos</span>
                  <ul className="client-form__benefits">
                    {selectedPlan.benefits.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </section>
      </div>

      <div className="client-form__actions">
        <Link to="/clientes" className="btn btn-ghost">
          Cancelar
        </Link>
        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Registrando…' : 'Registrar cliente'}
        </button>
      </div>
    </form>
  )
}
