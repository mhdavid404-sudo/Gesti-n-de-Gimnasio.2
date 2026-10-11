import { Link } from 'react-router-dom'
import './Breadcrumbs.css'

export interface BreadcrumbItem {
  label: string
  to?: string
}

/**
 * Migas de pan reutilizables — pensadas sobre todo para Detalle de Cliente
 * (`ClientDetailPage.tsx`), que hoy solo ofrece "Volver a clientes" dentro
 * del estado de error, sin ninguna ruta de regreso visible en el caso
 * normal (ver docs/REVISION-UX.md, heurística "Control y libertad del
 * usuario"). No se conecta todavía a esa pantalla porque está fuera del
 * alcance de esta tarea (solo lectura de las páginas que no sean Dashboard
 * — ver encargo); queda lista para que el trabajo que SÍ edite
 * ClientDetailPage.tsx la use así:
 *
 *   <Breadcrumbs items={[{ label: 'Clientes', to: '/clientes' }, { label: user.full_name }]} />
 *
 * Separador de texto ("/"), no un ícono de flecha — consistente con el
 * resto del sistema de íconos dibujados a mano (ver components/layout/icons.tsx).
 */
export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav className="breadcrumbs" aria-label="Migas de pan">
      <ol className="breadcrumbs__list">
        {items.map((item, index) => {
          const isLast = index === items.length - 1
          return (
            <li key={`${item.label}-${index}`} className="breadcrumbs__item">
              {item.to && !isLast ? (
                <Link to={item.to} className="breadcrumbs__link">
                  {item.label}
                </Link>
              ) : (
                <span className="breadcrumbs__current" aria-current={isLast ? 'page' : undefined}>
                  {item.label}
                </span>
              )}
              {!isLast && <span className="breadcrumbs__separator">/</span>}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
