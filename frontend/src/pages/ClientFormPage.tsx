import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { useAuth } from '../hooks/useAuth'
import { membershipPlans } from '../mocks/data'
import type { AuthUser } from '../api/authStorage'
import type { ClientRegisterPayload, ClientRegisterResponse } from '../types/api'
import type { PaymentMethod } from '../types/models'
import './ClientFormPage.css'

const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'tarjeta', label: 'Tarjeta' },
  { value: 'transferencia', label: 'Transferencia' },
]

const todayIso = () => new Date().toISOString().slice(0, 10)

type FormField = 'fullName' | 'email' | 'phone' | 'birthDate' | 'address'
type FormErrors = Partial<Record<FormField, string>>

/**
 * Alta de cliente — SOLO la sección "Datos del cliente" se conecta a
 * `POST /clients` real en esta tarea (DECISIONES.md, módulo Clientes,
 * Entrega 2). "Membresía y pago inicial" sigue siendo SOLO UI/mock: esos
 * módulos (Planes/Membresías, Pagos) no existen todavía, y el mensaje de
 * éxito tras guardar NO debe insinuar que el pago se registró (solo se
 * confirma lo que de verdad se persistió: el cliente).
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

  // --- Membresía y pago inicial (SOLO UI/mock -- ver docstring arriba) ---
  const [planId, setPlanId] = useState<number>(membershipPlans[0]?.id ?? 0)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('efectivo')
  const [amount, setAmount] = useState<number>(membershipPlans[0]?.price ?? 0)
  const [paymentDate, setPaymentDate] = useState(todayIso)

  const [errors, setErrors] = useState<FormErrors>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const selectedPlan = useMemo(() => membershipPlans.find((p) => p.id === planId), [planId])

  useEffect(() => {
    apiFetch<AuthUser[]>('/users?role=entrenador')
      .then(setTrainers)
      .catch(() => setTrainersError('No se pudo cargar la lista de entrenadores.'))
  }, [])

  const handlePlanChange = (id: number) => {
    setPlanId(id)
    const plan = membershipPlans.find((p) => p.id === id)
    if (plan) setAmount(plan.price)
  }

  // Limpia el error de UN campo en cuanto el usuario vuelve a escribir en
  // él — es la señal de "la interfaz escuchó" (en vez de obligar a
  // re-enviar el formulario para ver si ya quedó bien).
  const clearError = (field: FormField) => {
    setErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev))
  }

  const validate = (): FormErrors => {
    const next: FormErrors = {}
    if (!fullName.trim()) next.fullName = 'Ingresa el nombre completo.'
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) next.email = 'Ingresa un correo válido.'
    if (phone.replace(/\D/g, '').length < 10) next.phone = 'El teléfono debe tener al menos 10 dígitos.'
    if (!birthDate) next.birthDate = 'Selecciona una fecha de nacimiento.'
    if (!address.trim()) next.address = 'Ingresa una dirección.'
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

    setIsSubmitting(true)
    try {
      const response = await apiFetch<ClientRegisterResponse>('/clients', {
        method: 'POST',
        body: payload,
      })

      // Mensaje honesto: solo se confirma lo que realmente se persistió (el
      // cliente) -- la membresía/pago de la otra sección NO se registró,
      // ningún módulo real existe todavía para eso (ver docstring arriba).
      navigate('/clientes', {
        state: {
          toast: `Cliente "${response.client.full_name}" registrado. Contraseña temporal para su primer inicio de sesión: ${response.temporary_password} (cópiala y compártela con el cliente; no se mostrará de nuevo).`,
        },
      })
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
            Alta de membresía y registro del primer pago (RF004 / RF005) — todavía no conectado a un
            backend real; estos módulos se construyen en una tarea posterior.
          </p>

          <div className="client-form__field">
            <span className="field-label">Plan</span>
            <div className="client-form__plans" role="radiogroup" aria-label="Plan de membresía">
              {membershipPlans.map((plan) => (
                <label key={plan.id} className="client-form__plan" data-selected={plan.id === planId}>
                  <input
                    type="radio"
                    name="plan"
                    value={plan.id}
                    checked={plan.id === planId}
                    onChange={() => handlePlanChange(plan.id)}
                  />
                  <span className="client-form__plan-name">{plan.name}</span>
                  <span className="client-form__plan-price">${plan.price.toLocaleString('es-MX')}/mes</span>
                </label>
              ))}
            </div>
          </div>

          <div className="client-form__row">
            <div className="client-form__field">
              <label className="field-label" htmlFor="paymentMethod">
                Método de pago
              </label>
              <select
                id="paymentMethod"
                className="input"
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
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
                onChange={(e) => setAmount(Number(e.target.value))}
                required
              />
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
