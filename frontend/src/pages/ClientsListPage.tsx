import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { StatusPill } from '../components/ui/StatusPill'
import { clientListRows } from '../mocks/data'
import './ClientsListPage.css'

interface ClientsListLocationState {
  toast?: string
}

export function ClientsListPage() {
  const [query, setQuery] = useState('')
  const location = useLocation()
  const navigate = useNavigate()

  const initialToast = (location.state as ClientsListLocationState | null)?.toast ?? null
  const [toast, setToast] = useState<string | null>(initialToast)

  // El mensaje de éxito viaja como router state desde /clientes/nuevo (mock,
  // sin backend real). Se limpia del history en cuanto se muestra para que
  // un refresh o un "atrás" del navegador no lo repita.
  useEffect(() => {
    if (initialToast) {
      navigate('.', { replace: true, state: null })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return clientListRows
    return clientListRows.filter(
      (row) => row.fullName.toLowerCase().includes(q) || row.email.toLowerCase().includes(q),
    )
  }, [query])

  return (
    <div className="clients-page">
      {toast && (
        <div className="clients-page__toast" role="status">
          <span>{toast}</span>
          <button
            type="button"
            className="clients-page__toast-dismiss"
            onClick={() => setToast(null)}
            aria-label="Cerrar aviso"
          >
            ×
          </button>
        </div>
      )}

      <div className="clients-page__toolbar">
        <input
          className="input clients-page__search"
          placeholder="Buscar por nombre o correo…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Buscar cliente"
        />
        <span className="clients-page__count">{filtered.length} clientes</span>
        <span className="clients-page__toolbar-spacer" />
        <Link to="/clientes/nuevo" className="btn btn-primary">
          + Nuevo cliente
        </Link>
      </div>

      <div className="card clients-page__table-wrap">
        <table className="clients-page__table">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Contacto</th>
              <th>Entrenador</th>
              <th>Plan</th>
              <th>Membresía</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, index) => (
              <tr
                key={row.clientProfileId}
                // Stagger corto (ver ClientsListPage.css, tarea 3): el delay
                // crece por fila hasta un tope de 12 para que una tabla larga
                // no tarde segundos en terminar de aparecer. Al depender del
                // `key`, React solo remonta (y por lo tanto re-anima) filas
                // que son nuevas en el DOM — escribir en el buscador no
                // reinicia esto para las filas que ya estaban visibles.
                style={{ animationDelay: `${Math.min(index, 12) * 45}ms` }}
              >
                <td>
                  <span className="clients-page__name">{row.fullName}</span>
                </td>
                <td>
                  <div className="clients-page__contact">
                    <span>{row.email}</span>
                    <span className="clients-page__phone">{row.phone}</span>
                  </div>
                </td>
                <td>{row.trainerName}</td>
                <td>{row.planName}</td>
                <td>
                  <StatusPill status={row.membershipStatus} />
                </td>
                <td>
                  <Link to={`/clientes/${row.clientProfileId}`} className="btn btn-ghost clients-page__view">
                    Ver detalle
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
