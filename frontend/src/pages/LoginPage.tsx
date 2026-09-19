import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './LoginPage.css'

/**
 * Pantalla de Login — SOLO UI (Entrega 1).
 * No hay validación real ni conexión a backend: cualquier submit navega
 * directo al dashboard, tal como especifica el alcance de la entrega.
 */
export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('marisol@strongeraragon.mx')
  const [password, setPassword] = useState('')

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    navigate('/dashboard')
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
          <p className="login__helper">
            Prototipo de Entrega 1 — este formulario no valida credenciales todavía,
            cualquier dato te lleva al panel.
          </p>

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

          <button type="submit" className="btn btn-primary login__submit">
            Entrar al panel
          </button>

          <p className="login__footnote">
            El control de acceso por rol (Admin / Entrenador / Cliente) se activa en la
            Entrega 2, cuando exista backend real.
          </p>
        </form>
      </section>
    </div>
  )
}
