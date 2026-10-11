import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import './LoginPage.css'

/**
 * Pantalla de Login — conectada al backend real (Entrega 2, RF001).
 */
export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('marisol@strongeraragon.mx')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="login">
      <Link to="/" className="login__back-link">
        ← Volver al inicio
      </Link>

      <section className="login__hero">
        <div className="login__hero-brand">
          <div className="sidebar__brand-mark login__hero-mark">SA</div>
          <span>Stronger Aragón</span>
        </div>

        <div className="login__hero-stat">
          <div className="login__hero-stat-block">
            <span className="login__hero-stat-tag">Antes</span>
            <div className="login__hero-stat-value">2 turnos</div>
          </div>
          <div className="login__hero-stat-divider" />
          <div className="login__hero-stat-block">
            <span className="login__hero-stat-tag">Ahora</span>
            <div className="login__hero-stat-value">1 sistema</div>
          </div>
        </div>
        <p className="login__hero-copy">
          Antes: una hoja de Excel por turno, sin cruce de información. Ahora: un solo
          padrón de clientes, membresías y pagos, visible para toda la administración
          al mismo tiempo.
        </p>

        <ul className="login__hero-list">
          <li>Membresías vencidas o por vencer, siempre visibles</li>
          <li>Pagos con historial por cliente, no por turno</li>
          <li>Rutinas, dietas y progreso en un solo lugar</li>
        </ul>
      </section>

      <section className="login__panel">
        <form className="login__card card" onSubmit={handleSubmit}>
          <span className="eyebrow">Acceso al sistema</span>
          <h1 className="login__title">Iniciar sesión</h1>
          <p className="login__helper">Ingresa con tu correo y contraseña registrados en el sistema.</p>

          <div className="login__field">
            <label className="field-label" htmlFor="email">
              Correo
            </label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tucorreo@strongeraragon.mx"
              autoComplete="username"
            />
          </div>

          <div className="login__field">
            <label className="field-label" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="btn btn-primary login__submit" disabled={isSubmitting}>
            {isSubmitting ? 'Entrando…' : 'Entrar al panel'}
          </button>

          <p className="login__footnote">
            El control de acceso por rol (Admin / Entrenador / Cliente) ya esta activo en el
            backend.
          </p>
        </form>
      </section>
    </div>
  )
}
