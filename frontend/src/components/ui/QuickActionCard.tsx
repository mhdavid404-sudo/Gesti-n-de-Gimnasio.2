import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import './QuickActionCard.css'

interface QuickActionCardProps {
  to: string
  title: string
  description: string
  icon: ReactNode
  /** 'primary' resalta la acción más relevante de la sección (una sola por vista). */
  tone?: 'primary' | 'neutral'
}

/**
 * Tarjeta de acción grande para la zona "Qué puedo hacer" del panel (ver
 * DashboardPage.tsx) — la respuesta directa al feedback de la profesora:
 * "necesito ver al entrar qué puedo hacer". El título siempre empieza con
 * el verbo ("Registrar cliente", nunca "Clientes").
 *
 * Es un <Link> real (navega), no un botón decorativo — por eso sí lleva
 * feedback de presión (:active, ver QuickActionCard.css), siguiendo el
 * mismo criterio de "no animar affordance que no existe" ya documentado en
 * DECISIONES.md para las tarjetas de solo lectura del resto del sistema.
 */
export function QuickActionCard({ to, title, description, icon, tone = 'neutral' }: QuickActionCardProps) {
  return (
    <Link to={to} className="quick-action-card" data-tone={tone}>
      <span className="quick-action-card__icon">{icon}</span>
      <span className="quick-action-card__text">
        <span className="quick-action-card__title">{title}</span>
        <span className="quick-action-card__description">{description}</span>
      </span>
    </Link>
  )
}
