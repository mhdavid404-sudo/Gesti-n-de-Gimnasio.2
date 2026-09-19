import { useState } from 'react'
import { Link } from 'react-router-dom'
import logoStronger from '../assets/logo-stronger.jpg'
import { useScrollReveal } from '../hooks/useScrollReveal'
import { membershipPlans } from '../mocks/data'
import './LandingPage.css'

/**
 * Landing pública de Stronger Aragón — ruta "/".
 *
 * Identidad de marca REAL (logo importado tal cual, paleta extraída del
 * degradado verde del logo), completamente separada del tema
 * grafito/cobre del panel interno (ver src/styles/theme.css, intacto).
 * Todas las variables de color/tipografía de esta pieza viven bajo la
 * clase raíz `.landing`, nunca en :root.
 *
 * Zonas marcadas con `--*-image` son placeholder gráfico (gradientes +
 * geometría, sin fotografía real) listas para recibir una foto real
 * después con solo sobreescribir esa custom property.
 */

const NAV_LINKS = [
  { href: '#clases', label: 'Clases' },
  { href: '#instalaciones', label: 'Instalaciones' },
  { href: '#planes', label: 'Planes' },
]

const SCHEDULE = [
  { day: 'Lunes a viernes', slot: '6:00 – 10:00 hrs' },
  { day: 'Lunes a viernes', slot: '17:00 – 21:00 hrs' },
  { day: 'Sábados', slot: '8:00 – 11:00 hrs' },
]

const FACILITIES = [
  {
    key: 'pesas',
    title: 'Peso libre',
    copy: 'Barras olímpicas, discos y racks de sentadilla sin fila de espera.',
    icon: IconBarbell,
  },
  {
    key: 'box',
    title: 'Ring de Box',
    copy: 'Espacio dedicado a costales, guantes y trabajo de sombra real.',
    icon: IconGlove,
  },
  {
    key: 'funcional',
    title: 'Área funcional',
    copy: 'Kettlebells, cuerdas y circuitos de acondicionamiento físico.',
    icon: IconKettlebell,
  },
]

export function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)

  // Scroll-reveal editorial (ver CLAUDE.md tarea 2) — el hero queda fuera
  // a propósito: ya está visible desde el primer frame, no hay "revelado"
  // posible en lo primero que ve el usuario.
  const valueReveal = useScrollReveal<HTMLElement>()
  const plansReveal = useScrollReveal<HTMLElement>()
  const classesReveal = useScrollReveal<HTMLElement>()
  const facilitiesReveal = useScrollReveal<HTMLElement>()
  const footerReveal = useScrollReveal<HTMLElement>()

  return (
    <div className="landing">
      <header className="landing-header">
        <div className="landing-header__inner">
          <a href="#top" className="landing-header__brand" aria-label="Stronger Aragón, ir al inicio">
            <img src={logoStronger} alt="Stronger Aragón — Centro de Entrenamiento Integral" className="landing-header__logo" />
          </a>

          <nav className="landing-header__nav landing-header__nav--desktop" aria-label="Navegación principal">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="landing-header__link">
                {link.label}
              </a>
            ))}
          </nav>

          <div className="landing-header__actions">
            <Link to="/login" className="lp-btn lp-btn--brand landing-header__cta">
              Entrar al panel
            </Link>

            <button
              type="button"
              className="landing-header__toggle"
              aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
              aria-expanded={menuOpen}
              aria-controls="landing-mobile-nav"
              onClick={() => setMenuOpen((open) => !open)}
            >
              {menuOpen ? <IconClose /> : <IconMenu />}
            </button>
          </div>
        </div>

        {menuOpen ? (
          <nav id="landing-mobile-nav" className="landing-header__nav landing-header__nav--mobile" aria-label="Navegación móvil">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="landing-header__link" onClick={() => setMenuOpen(false)}>
                {link.label}
              </a>
            ))}
          </nav>
        ) : null}
      </header>

      <main id="top">
        <section className="lp-hero">
          <div className="lp-hero__backdrop" aria-hidden="true" />
          <div className="lp-hero__grain" aria-hidden="true" />
          <div className="lp-hero__content">
            <h1 className="lp-hero__title">
              ENTRENA
              <br />
              COMO BESTIA
            </h1>
            <p className="lp-hero__copy">
              Piso de pesas, ring de box y área funcional bajo un mismo techo. Stronger
              Aragón no es para pasar el rato: aquí se carga la barra y se entrena en
              serio, todos los días.
            </p>
            <div className="lp-hero__actions">
              <a href="#planes" className="lp-btn lp-btn--brand lp-btn--lg">
                Ver planes
              </a>
              <Link to="/login" className="lp-btn lp-btn--ghost lp-btn--lg">
                Entrar al panel
              </Link>
            </div>
          </div>
        </section>

        <section className="lp-value" ref={valueReveal.ref} data-reveal={valueReveal.visible ? 'visible' : 'hidden'}>
          <div className="lp-value__graphic" aria-hidden="true">
            <span className="lp-value__graphic-figure">360°</span>
            <span className="lp-value__graphic-label">Entrenamiento integral</span>
          </div>

          <div className="lp-value__text">
            <h2 className="lp-section-title">Un plan, un entrenador, resultados que se miden</h2>
            <p className="lp-value__lead">
              Nada de rutinas genéricas de internet. Cada cliente de Stronger Aragón
              entrena con seguimiento real: rutina asignada, dieta asignada y progreso
              corporal registrado cada quincena — no adivinamos, medimos.
            </p>
            <ul className="lp-value__list">
              <li>Rutina de fuerza o hipertrofia diseñada por tu entrenador</li>
              <li>Plan de dieta ajustado a tu objetivo, no una tabla genérica</li>
              <li>Evaluación de progreso con cifras, no con espejo</li>
            </ul>
          </div>
        </section>

        <section
          id="planes"
          className="lp-plans"
          ref={plansReveal.ref}
          data-reveal={plansReveal.visible ? 'visible' : 'hidden'}
        >
          <h2 className="lp-section-title lp-plans__title">Elige tu plan</h2>
          <p className="lp-plans__subtitle">
            Tres niveles de acceso, sin letras chiquitas. Cambia o cancela cuando
            quieras en recepción.
          </p>

          <div className="lp-plans__grid">
            {membershipPlans.map((plan) => {
              const featured = plan.name === 'VIP'
              return (
                <article
                  key={plan.id}
                  className={`lp-plan-card${featured ? ' lp-plan-card--featured' : ''}`}
                >
                  {featured ? <span className="lp-plan-card__badge">Más popular</span> : null}
                  <span className="lp-plan-card__name">{plan.name}</span>
                  <div className="lp-plan-card__price">
                    ${plan.price.toLocaleString('es-MX')}
                    <span>/mes</span>
                  </div>
                  <p className="lp-plan-card__description">{plan.description}</p>
                  <ul className="lp-plan-card__benefits">
                    {plan.benefits.map((benefit) => (
                      <li key={benefit}>{benefit}</li>
                    ))}
                  </ul>
                  <Link
                    to="/login"
                    className={`lp-btn ${featured ? 'lp-btn--brand' : 'lp-btn--ghost'} lp-plan-card__cta`}
                  >
                    Quiero este plan
                  </Link>
                </article>
              )
            })}
          </div>
        </section>

        <section
          id="clases"
          className="lp-classes"
          ref={classesReveal.ref}
          data-reveal={classesReveal.visible ? 'visible' : 'hidden'}
        >
          <div className="lp-classes__inner">
            <div className="lp-classes__intro">
              <h2 className="lp-section-title">Clases de Box</h2>
              <p>
                Cupo limitado por sesión para que el entrenador vea a cada quien.
                Preséntate 10 minutos antes con vendas o guantes propios.
              </p>
            </div>

            <table className="lp-classes__table">
              <caption className="lp-classes__caption">Horario semanal de clases de Box</caption>
              <thead>
                <tr>
                  <th scope="col">Día</th>
                  <th scope="col">Horario</th>
                </tr>
              </thead>
              <tbody>
                {SCHEDULE.map((row) => (
                  <tr key={`${row.day}-${row.slot}`}>
                    <td>{row.day}</td>
                    <td>{row.slot}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section
          id="instalaciones"
          className="lp-facilities"
          ref={facilitiesReveal.ref}
          data-reveal={facilitiesReveal.visible ? 'visible' : 'hidden'}
        >
          <h2 className="lp-section-title lp-facilities__title">Conoce las instalaciones</h2>

          <div className="lp-facilities__grid">
            {FACILITIES.map(({ key, title, copy, icon: Icon }) => (
              <figure key={key} className="lp-facility-card">
                <div className={`lp-facility-card__graphic lp-facility-card__graphic--${key}`} aria-hidden="true">
                  <Icon className="lp-facility-card__icon" />
                </div>
                <figcaption>
                  <span className="lp-facility-card__title">{title}</span>
                  <p>{copy}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      </main>

      <footer
        className="landing-footer"
        ref={footerReveal.ref}
        data-reveal={footerReveal.visible ? 'visible' : 'hidden'}
      >
        <div className="landing-footer__inner">
          <div className="landing-footer__brand">
            <img src={logoStronger} alt="Stronger Aragón" className="landing-footer__logo" />
            <p>Centro de Entrenamiento Integral. Piso de pesas, box y funcional.</p>
          </div>

          <div className="landing-footer__contact">
            <span className="landing-footer__heading">Contacto</span>
            <p>Stronger Aragón — Aragón, Ciudad de México</p>
            <p>55 0000 0000</p>
            <p>contacto@strongeraragon.mx</p>
          </div>

          <div className="landing-footer__social">
            <span className="landing-footer__heading">Síguenos</span>
            <div className="landing-footer__social-links">
              <a href="#" aria-label="Stronger Aragón en Instagram" className="landing-footer__social-link">
                <IconInstagram />
              </a>
              <a href="#" aria-label="Stronger Aragón en Facebook" className="landing-footer__social-link">
                <IconFacebook />
              </a>
            </div>
          </div>
        </div>

        <div className="landing-footer__bottom">
          <span>© 2026 Stronger Aragón. Todos los derechos reservados.</span>
          <Link to="/login">Acceso administrativo</Link>
        </div>
      </footer>
    </div>
  )
}

/* -----------------------------------------------------------------------
   Iconos de línea propios de la landing — mismo lenguaje de trazo que el
   panel interno (currentColor, trazo uniforme) pero self-contained aquí.
----------------------------------------------------------------------- */
type IconProps = { className?: string }

const iconBase = {
  width: 22,
  height: 22,
  viewBox: '0 0 22 22',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

function IconBarbell({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className}>
      <line x1="2.4" y1="11" x2="19.6" y2="11" />
      <rect x="4" y="7.2" width="2.2" height="7.6" rx="0.6" />
      <rect x="15.8" y="7.2" width="2.2" height="7.6" rx="0.6" />
      <rect x="1.2" y="8.8" width="1.8" height="4.4" rx="0.5" />
      <rect x="19" y="8.8" width="1.8" height="4.4" rx="0.5" />
    </svg>
  )
}

function IconGlove({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className}>
      <path d="M6.4 10.2V5.6a1.8 1.8 0 0 1 3.6 0v3.2" />
      <path d="M10 8.6V4.4a1.8 1.8 0 0 1 3.6 0v4.6" />
      <path d="M13.6 8.8V5.6a1.8 1.8 0 0 1 3.6 0v6.8c0 3.4-2.2 6-6 6h-1.4c-2.8 0-4.6-1.5-5.6-3.6l-2-4.2a1.5 1.5 0 0 1 2.7-1.3l1.5 2.5" />
    </svg>
  )
}

function IconKettlebell({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className}>
      <path d="M8.2 6.4V5.2a2.8 2.8 0 0 1 5.6 0v1.2" />
      <ellipse cx="11" cy="13.2" rx="6.2" ry="5.4" />
      <path d="M7.6 6.4h6.8a1.6 1.6 0 0 1 1.6 1.6v1.4H6V8a1.6 1.6 0 0 1 1.6-1.6Z" />
    </svg>
  )
}

function IconMenu({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className} strokeWidth={1.8}>
      <line x1="3" y1="6.5" x2="19" y2="6.5" />
      <line x1="3" y1="11" x2="19" y2="11" />
      <line x1="3" y1="15.5" x2="19" y2="15.5" />
    </svg>
  )
}

function IconClose({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className} strokeWidth={1.8}>
      <line x1="4.5" y1="4.5" x2="17.5" y2="17.5" />
      <line x1="17.5" y1="4.5" x2="4.5" y2="17.5" />
    </svg>
  )
}

function IconInstagram({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className}>
      <rect x="3" y="3" width="16" height="16" rx="4.5" />
      <circle cx="11" cy="11" r="4" />
      <circle cx="15.6" cy="6.4" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}

function IconFacebook({ className }: IconProps) {
  return (
    <svg {...iconBase} className={className}>
      <path d="M13.2 8.2h-2V6.6c0-.6.4-1 1-1h1V3h-1.8A2.8 2.8 0 0 0 8.6 5.8v2.4H6.8v2.6h1.8V19h2.6v-8.2h1.8Z" />
    </svg>
  )
}
