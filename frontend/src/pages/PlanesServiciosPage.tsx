import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { apiFetch, ApiError } from '../api/client'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { Tabs } from '../components/ui/Tabs'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type {
  ApiBillingPeriod,
  ApiMembershipPlan,
  ApiService,
  MembershipPlanCreatePayload,
  ServiceCreatePayload,
} from '../types/api'
import './PlanesServiciosPage.css'

const TABS = [
  { id: 'planes', label: 'Planes' },
  { id: 'servicios', label: 'Servicios extra' },
]

const BILLING_PERIODS: { value: ApiBillingPeriod; label: string }[] = [
  { value: 'unico', label: 'Pago único' },
  { value: 'mensual', label: 'Mensual' },
  { value: 'periodo', label: 'Dura lo que la membresía' },
]

const billingPeriodLabel = (value: ApiBillingPeriod): string =>
  BILLING_PERIODS.find((p) => p.value === value)?.label ?? value

/**
 * Pantalla única "Planes y servicios" (Entrega 3, Fase 2 -- amplía
 * RF004/RF005): administración completa del catálogo (solo admin). Dos
 * pestañas con la MISMA interfaz de alta/edición/eliminación-o-
 * desactivación: Planes y Servicios extra, más qué servicios incluye
 * cada plan (checkboxes).
 *
 * `MembershipsPage.tsx` conserva su propio alta rápida de plan (RF004,
 * Entrega 2) -- esta pantalla es la administración COMPLETA (editar,
 * eliminar/desactivar, servicios incluidos), no la reemplaza.
 */
export function PlanesServiciosPage() {
  const { logout } = useAuth()
  const [activeTab, setActiveTab] = useState('planes')

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

  // --- Catálogos compartidos entre las dos pestañas -------------------------
  const [plans, setPlans] = useState<ApiMembershipPlan[] | null>(null)
  const [plansLoading, setPlansLoading] = useState(true)
  const [plansError, setPlansError] = useState<string | null>(null)

  const loadPlans = () => {
    setPlansLoading(true)
    setPlansError(null)
    apiFetch<ApiMembershipPlan[]>('/membership-plans')
      .then(setPlans)
      .catch((err: unknown) => handleAuthError(err, setPlansError))
      .finally(() => setPlansLoading(false))
  }

  const [services, setServices] = useState<ApiService[] | null>(null)
  const [servicesLoading, setServicesLoading] = useState(true)
  const [servicesError, setServicesError] = useState<string | null>(null)

  const loadServices = () => {
    setServicesLoading(true)
    setServicesError(null)
    apiFetch<ApiService[]>('/services')
      .then(setServices)
      .catch((err: unknown) => handleAuthError(err, setServicesError))
      .finally(() => setServicesLoading(false))
  }

  useEffect(() => {
    loadPlans()
    loadServices()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // --- Alta/edición de plan ---------------------------------------------
  const [showPlanForm, setShowPlanForm] = useState(false)
  const [editingPlanId, setEditingPlanId] = useState<number | null>(null)
  const [planName, setPlanName] = useState('')
  const [planPrice, setPlanPrice] = useState('')
  const [planDuration, setPlanDuration] = useState('')
  const [planDescription, setPlanDescription] = useState('')
  const [planBenefits, setPlanBenefits] = useState('')
  const [planServerError, setPlanServerError] = useState<string | null>(null)
  const [isSubmittingPlan, setIsSubmittingPlan] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const resetPlanForm = () => {
    setEditingPlanId(null)
    setPlanName('')
    setPlanPrice('')
    setPlanDuration('')
    setPlanDescription('')
    setPlanBenefits('')
    setPlanServerError(null)
  }

  const openNewPlanForm = () => {
    resetPlanForm()
    setShowPlanForm(true)
  }

  const openEditPlanForm = (plan: ApiMembershipPlan) => {
    setEditingPlanId(plan.id)
    setPlanName(plan.name)
    setPlanPrice(plan.price)
    setPlanDuration(String(plan.duration_days))
    setPlanDescription(plan.description ?? '')
    setPlanBenefits(plan.benefits.join('\n'))
    setPlanServerError(null)
    setShowPlanForm(true)
  }

  const handleSubmitPlan = async (event: FormEvent) => {
    event.preventDefault()
    setPlanServerError(null)

    const priceValue = Number(planPrice)
    const durationValue = Number(planDuration)
    if (!planName.trim()) return setPlanServerError('Ingresa el nombre del plan.')
    if (!planPrice || Number.isNaN(priceValue) || priceValue <= 0) {
      return setPlanServerError('Ingresa un precio mayor a 0.')
    }
    if (!planDuration || Number.isNaN(durationValue) || durationValue <= 0 || !Number.isInteger(durationValue)) {
      return setPlanServerError('Ingresa una duración en días (número entero mayor a 0).')
    }

    const payload: MembershipPlanCreatePayload = {
      name: planName.trim(),
      price: priceValue,
      duration_days: durationValue,
      description: planDescription.trim() || null,
      benefits: planBenefits
        .split('\n')
        .map((b) => b.trim())
        .filter(Boolean),
    }

    setIsSubmittingPlan(true)
    try {
      if (editingPlanId != null) {
        const updated = await apiFetch<ApiMembershipPlan>(`/membership-plans/${editingPlanId}`, {
          method: 'PATCH',
          body: payload,
        })
        setPlans((prev) => (prev ?? []).map((p) => (p.id === updated.id ? updated : p)))
        setToast(`Plan "${updated.name}" actualizado.`)
      } else {
        const created = await apiFetch<ApiMembershipPlan>('/membership-plans', { method: 'POST', body: payload })
        setPlans((prev) => [...(prev ?? []), created])
        setToast(`Plan "${created.name}" creado.`)
      }
      setShowPlanForm(false)
      resetPlanForm()
    } catch (err) {
      handleAuthError(err, setPlanServerError, () => setPlanServerError('No tienes permiso para administrar planes.'))
    } finally {
      setIsSubmittingPlan(false)
    }
  }

  // --- Eliminar/desactivar plan -------------------------------------------
  const [planToDelete, setPlanToDelete] = useState<ApiMembershipPlan | null>(null)
  const [isDeletingPlan, setIsDeletingPlan] = useState(false)

  const handleDeletePlan = async () => {
    if (!planToDelete) return
    setIsDeletingPlan(true)
    try {
      await apiFetch<ApiMembershipPlan>(`/membership-plans/${planToDelete.id}`, { method: 'DELETE' })
      const refreshed = await apiFetch<ApiMembershipPlan[]>('/membership-plans')
      const stillExists = refreshed.some((p) => p.id === planToDelete.id)
      setPlans(refreshed)
      setToast(
        stillExists
          ? `"${planToDelete.name}" tiene membresías contratadas: se desactivó en vez de eliminarse.`
          : `"${planToDelete.name}" se eliminó (no tenía membresías contratadas).`,
      )
    } catch (err) {
      handleAuthError(err, setToast, () => setToast('No tienes permiso para eliminar planes.'))
    } finally {
      setIsDeletingPlan(false)
      setPlanToDelete(null)
    }
  }

  // --- Servicios incluidos por plan (plan_services), cargados al expandir --
  const [planServicesById, setPlanServicesById] = useState<Map<number, ApiService[]>>(new Map())
  const [loadingPlanServicesIds, setLoadingPlanServicesIds] = useState<Set<number>>(new Set())
  const [togglingServiceKey, setTogglingServiceKey] = useState<string | null>(null)

  const loadPlanServices = (planId: number) => {
    setLoadingPlanServicesIds((prev) => new Set(prev).add(planId))
    apiFetch<ApiService[]>(`/membership-plans/${planId}/services`)
      .then((items) => setPlanServicesById((prev) => new Map(prev).set(planId, items)))
      .catch(() => setPlanServicesById((prev) => new Map(prev).set(planId, [])))
      .finally(() =>
        setLoadingPlanServicesIds((prev) => {
          const next = new Set(prev)
          next.delete(planId)
          return next
        }),
      )
  }

  const toggleServiceInPlan = async (planId: number, service: ApiService, included: boolean) => {
    const key = `${planId}:${service.id}`
    setTogglingServiceKey(key)
    try {
      if (included) {
        await apiFetch<void>(`/membership-plans/${planId}/services/${service.id}`, { method: 'DELETE' })
      } else {
        await apiFetch<ApiService>(`/membership-plans/${planId}/services`, {
          method: 'POST',
          body: { service_id: service.id },
        })
      }
      loadPlanServices(planId)
    } catch (err) {
      handleAuthError(err, setToast, () => setToast('No tienes permiso para administrar los servicios de un plan.'))
    } finally {
      setTogglingServiceKey(null)
    }
  }

  // --- Alta/edición de servicio --------------------------------------------
  const [showServiceForm, setShowServiceForm] = useState(false)
  const [editingServiceId, setEditingServiceId] = useState<number | null>(null)
  const [serviceName, setServiceName] = useState('')
  const [servicePrice, setServicePrice] = useState('')
  const [serviceBillingPeriod, setServiceBillingPeriod] = useState<ApiBillingPeriod>('mensual')
  const [serviceDescription, setServiceDescription] = useState('')
  const [serviceServerError, setServiceServerError] = useState<string | null>(null)
  const [isSubmittingService, setIsSubmittingService] = useState(false)

  const resetServiceForm = () => {
    setEditingServiceId(null)
    setServiceName('')
    setServicePrice('')
    setServiceBillingPeriod('mensual')
    setServiceDescription('')
    setServiceServerError(null)
  }

  const openNewServiceForm = () => {
    resetServiceForm()
    setShowServiceForm(true)
  }

  const openEditServiceForm = (service: ApiService) => {
    setEditingServiceId(service.id)
    setServiceName(service.name)
    setServicePrice(service.price)
    setServiceBillingPeriod(service.billing_period)
    setServiceDescription(service.description ?? '')
    setServiceServerError(null)
    setShowServiceForm(true)
  }

  const handleSubmitService = async (event: FormEvent) => {
    event.preventDefault()
    setServiceServerError(null)

    const priceValue = Number(servicePrice)
    if (!serviceName.trim()) return setServiceServerError('Ingresa el nombre del servicio.')
    if (!servicePrice || Number.isNaN(priceValue) || priceValue <= 0) {
      return setServiceServerError('Ingresa un precio mayor a 0.')
    }

    const payload: ServiceCreatePayload = {
      name: serviceName.trim(),
      price: priceValue,
      billing_period: serviceBillingPeriod,
      description: serviceDescription.trim() || null,
    }

    setIsSubmittingService(true)
    try {
      if (editingServiceId != null) {
        const updated = await apiFetch<ApiService>(`/services/${editingServiceId}`, { method: 'PATCH', body: payload })
        setServices((prev) => (prev ?? []).map((s) => (s.id === updated.id ? updated : s)))
        setToast(`Servicio "${updated.name}" actualizado.`)
      } else {
        const created = await apiFetch<ApiService>('/services', { method: 'POST', body: payload })
        setServices((prev) => [...(prev ?? []), created])
        setToast(`Servicio "${created.name}" creado.`)
      }
      setShowServiceForm(false)
      resetServiceForm()
    } catch (err) {
      handleAuthError(err, setServiceServerError, () =>
        setServiceServerError('No tienes permiso para administrar servicios.'),
      )
    } finally {
      setIsSubmittingService(false)
    }
  }

  // --- Eliminar/desactivar servicio ----------------------------------------
  const [serviceToDelete, setServiceToDelete] = useState<ApiService | null>(null)
  const [isDeletingService, setIsDeletingService] = useState(false)

  const handleDeleteService = async () => {
    if (!serviceToDelete) return
    setIsDeletingService(true)
    try {
      await apiFetch<ApiService>(`/services/${serviceToDelete.id}`, { method: 'DELETE' })
      const refreshed = await apiFetch<ApiService[]>('/services')
      const stillExists = refreshed.some((s) => s.id === serviceToDelete.id)
      setServices(refreshed)
      setToast(
        stillExists
          ? `"${serviceToDelete.name}" tiene contrataciones: se desactivó en vez de eliminarse.`
          : `"${serviceToDelete.name}" se eliminó (no tenía contrataciones).`,
      )
    } catch (err) {
      handleAuthError(err, setToast, () => setToast('No tienes permiso para eliminar servicios.'))
    } finally {
      setIsDeletingService(false)
      setServiceToDelete(null)
    }
  }

  return (
    <div className="plans-services-page">
      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}

      <Tabs items={TABS} activeId={activeTab} onChange={setActiveTab}>
        {activeTab === 'planes' && (
          <div className="plans-services-page__section">
            <div className="plans-services-page__toolbar">
              <button type="button" className="btn btn-primary" onClick={openNewPlanForm}>
                + Nuevo plan
              </button>
            </div>

            {showPlanForm && (
              <form className="card plans-services-page__inline-form" onSubmit={handleSubmitPlan}>
                {planServerError && <ErrorMessage title="No se pudo guardar el plan" message={planServerError} />}
                <div className="plans-services-page__form-row">
                  <div className="plans-services-page__field">
                    <label className="field-label" htmlFor="planName">
                      Nombre
                    </label>
                    <input id="planName" className="input" value={planName} onChange={(e) => setPlanName(e.target.value)} />
                  </div>
                  <div className="plans-services-page__field">
                    <label className="field-label" htmlFor="planPrice">
                      Precio mensual
                    </label>
                    <input
                      id="planPrice"
                      type="number"
                      min={0}
                      step="0.01"
                      className="input"
                      value={planPrice}
                      onChange={(e) => setPlanPrice(e.target.value)}
                    />
                  </div>
                  <div className="plans-services-page__field">
                    <label className="field-label" htmlFor="planDuration">
                      Duración (días)
                    </label>
                    <input
                      id="planDuration"
                      type="number"
                      min={1}
                      className="input"
                      value={planDuration}
                      onChange={(e) => setPlanDuration(e.target.value)}
                      placeholder="30"
                    />
                  </div>
                </div>
                <div className="plans-services-page__field">
                  <label className="field-label" htmlFor="planDescription">
                    Descripción (opcional)
                  </label>
                  <input
                    id="planDescription"
                    className="input"
                    value={planDescription}
                    onChange={(e) => setPlanDescription(e.target.value)}
                  />
                </div>
                <div className="plans-services-page__field">
                  <label className="field-label" htmlFor="planBenefits">
                    Beneficios (uno por línea)
                  </label>
                  <textarea
                    id="planBenefits"
                    className="input"
                    rows={3}
                    value={planBenefits}
                    onChange={(e) => setPlanBenefits(e.target.value)}
                    placeholder={'Acceso a área de pesas\nAcceso a cardio'}
                  />
                </div>
                <div className="plans-services-page__form-actions">
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => {
                      setShowPlanForm(false)
                      resetPlanForm()
                    }}
                  >
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={isSubmittingPlan}>
                    {isSubmittingPlan ? 'Guardando…' : editingPlanId != null ? 'Guardar cambios' : 'Crear plan'}
                  </button>
                </div>
              </form>
            )}

            {plansLoading ? (
              <div className="card">
                <LoadingState label="Cargando planes…" variant="skeleton" rows={3} />
              </div>
            ) : plansError ? (
              <ErrorMessage message={plansError} onRetry={loadPlans} />
            ) : !plans || plans.length === 0 ? (
              <div className="card">
                <EmptyState title="Todavía no hay planes" description='Crea el primero con "+ Nuevo plan".' />
              </div>
            ) : (
              <div className="plans-services-page__catalog">
                {plans.map((plan) => {
                  const included = planServicesById.get(plan.id)
                  const isLoadingIncluded = loadingPlanServicesIds.has(plan.id)
                  const includedIds = new Set((included ?? []).map((s) => s.id))
                  return (
                    <details
                      key={plan.id}
                      className="card plan-card"
                      onToggle={(e) => {
                        if ((e.target as HTMLDetailsElement).open && !planServicesById.has(plan.id)) {
                          loadPlanServices(plan.id)
                        }
                      }}
                    >
                      <summary>
                        <span className="plan-card__name">
                          {plan.name}
                          {!plan.is_active && <StatusPill status="inactivo" />}
                        </span>
                        <span className="plan-card__price">${Number(plan.price).toLocaleString('es-MX')}/mes</span>
                      </summary>

                      {plan.description && <p className="plan-card__description">{plan.description}</p>}
                      {plan.benefits.length > 0 && (
                        <ul className="plan-card__benefits">
                          {plan.benefits.map((b) => (
                            <li key={b}>{b}</li>
                          ))}
                        </ul>
                      )}

                      <div className="plan-card__actions">
                        <button type="button" className="btn btn-ghost" onClick={() => openEditPlanForm(plan)}>
                          Editar
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost plans-services-page__danger-btn"
                          onClick={() => setPlanToDelete(plan)}
                        >
                          Eliminar
                        </button>
                      </div>

                      <div className="plan-card__services">
                        <span className="field-label">Servicios incluidos</span>
                        {isLoadingIncluded || !services ? (
                          <LoadingState label="Cargando…" variant="skeleton" rows={2} />
                        ) : services.length === 0 ? (
                          <p className="plans-services-page__note">
                            Todavía no hay servicios en el catálogo -- agrega uno en la pestaña "Servicios extra".
                          </p>
                        ) : (
                          <ul className="plan-card__service-checklist">
                            {services.map((service) => {
                              const key = `${plan.id}:${service.id}`
                              return (
                                <li key={service.id}>
                                  <label>
                                    <input
                                      type="checkbox"
                                      checked={includedIds.has(service.id)}
                                      disabled={togglingServiceKey === key}
                                      onChange={() => toggleServiceInPlan(plan.id, service, includedIds.has(service.id))}
                                    />
                                    {service.name} (${Number(service.price).toLocaleString('es-MX')})
                                  </label>
                                </li>
                              )
                            })}
                          </ul>
                        )}
                      </div>
                    </details>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'servicios' && (
          <div className="plans-services-page__section">
            <div className="plans-services-page__toolbar">
              <button type="button" className="btn btn-primary" onClick={openNewServiceForm}>
                + Nuevo servicio
              </button>
            </div>

            {showServiceForm && (
              <form className="card plans-services-page__inline-form" onSubmit={handleSubmitService}>
                {serviceServerError && (
                  <ErrorMessage title="No se pudo guardar el servicio" message={serviceServerError} />
                )}
                <div className="plans-services-page__form-row">
                  <div className="plans-services-page__field">
                    <label className="field-label" htmlFor="serviceName">
                      Nombre
                    </label>
                    <input
                      id="serviceName"
                      className="input"
                      value={serviceName}
                      onChange={(e) => setServiceName(e.target.value)}
                    />
                  </div>
                  <div className="plans-services-page__field">
                    <label className="field-label" htmlFor="servicePrice">
                      Precio
                    </label>
                    <input
                      id="servicePrice"
                      type="number"
                      min={0}
                      step="0.01"
                      className="input"
                      value={servicePrice}
                      onChange={(e) => setServicePrice(e.target.value)}
                    />
                  </div>
                  <div className="plans-services-page__field">
                    <label className="field-label" htmlFor="serviceBillingPeriod">
                      Periodo de facturación
                    </label>
                    <select
                      id="serviceBillingPeriod"
                      className="input"
                      value={serviceBillingPeriod}
                      onChange={(e) => setServiceBillingPeriod(e.target.value as ApiBillingPeriod)}
                    >
                      {BILLING_PERIODS.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="plans-services-page__field">
                  <label className="field-label" htmlFor="serviceDescription">
                    Descripción (opcional)
                  </label>
                  <input
                    id="serviceDescription"
                    className="input"
                    value={serviceDescription}
                    onChange={(e) => setServiceDescription(e.target.value)}
                  />
                </div>
                <div className="plans-services-page__form-actions">
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => {
                      setShowServiceForm(false)
                      resetServiceForm()
                    }}
                  >
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={isSubmittingService}>
                    {isSubmittingService ? 'Guardando…' : editingServiceId != null ? 'Guardar cambios' : 'Crear servicio'}
                  </button>
                </div>
              </form>
            )}

            {servicesLoading ? (
              <div className="card">
                <LoadingState label="Cargando servicios…" variant="skeleton" rows={3} />
              </div>
            ) : servicesError ? (
              <ErrorMessage message={servicesError} onRetry={loadServices} />
            ) : !services || services.length === 0 ? (
              <div className="card">
                <EmptyState title="Todavía no hay servicios extra" description='Crea el primero con "+ Nuevo servicio".' />
              </div>
            ) : (
              <div className="card plans-services-page__table-wrap">
                <table className="plans-services-page__table">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Precio</th>
                      <th>Periodo</th>
                      <th>Estado</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {services.map((service) => (
                      <tr key={service.id}>
                        <td>
                          {service.name}
                          {service.description && (
                            <p className="plans-services-page__service-description">{service.description}</p>
                          )}
                        </td>
                        <td>${Number(service.price).toLocaleString('es-MX')}</td>
                        <td>{billingPeriodLabel(service.billing_period)}</td>
                        <td>
                          <StatusPill status={service.is_active ? 'activa' : 'inactivo'} />
                        </td>
                        <td className="plans-services-page__row-actions">
                          <button type="button" className="btn btn-ghost" onClick={() => openEditServiceForm(service)}>
                            Editar
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost plans-services-page__danger-btn"
                            onClick={() => setServiceToDelete(service)}
                          >
                            Eliminar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </Tabs>

      <ConfirmDialog
        open={planToDelete != null}
        title={`¿Eliminar el plan "${planToDelete?.name}"?`}
        description="Si tiene membresías contratadas se desactiva en vez de eliminarse (deja de ofrecerse, pero no rompe lo ya contratado)."
        confirmLabel={isDeletingPlan ? 'Eliminando…' : 'Eliminar'}
        onConfirm={handleDeletePlan}
        onCancel={() => setPlanToDelete(null)}
      />

      <ConfirmDialog
        open={serviceToDelete != null}
        title={`¿Eliminar el servicio "${serviceToDelete?.name}"?`}
        description="Si tiene contrataciones activas se desactiva en vez de eliminarse."
        confirmLabel={isDeletingService ? 'Eliminando…' : 'Eliminar'}
        onConfirm={handleDeleteService}
        onCancel={() => setServiceToDelete(null)}
      />
    </div>
  )
}
