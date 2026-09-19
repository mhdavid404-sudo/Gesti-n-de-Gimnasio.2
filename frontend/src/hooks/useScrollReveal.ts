import { useEffect, useRef, useState } from 'react'

/**
 * Entrada suave (fade + translateY) para secciones editoriales de la
 * landing al hacer scroll — ver CLAUDE.md, tarea 2.
 *
 * Solo tiene sentido en contenido de "primera vista" que se recorre una
 * vez (landing pública): NO se usa en las pantallas internas de gestión
 * (Dashboard, Clientes, etc.), que se cargan una vez por sesión de
 * trabajo y no se benefician de diferir su aparición.
 *
 * `{ once: true }` vía IntersectionObserver.unobserve — una sección que ya
 * entró no vuelve a ocultarse si el usuario sube y baja el scroll; eso
 * sería ruido, no la sorpresa/bienvenida de "primera vista" que se busca.
 */
export function useScrollReveal<T extends HTMLElement>() {
  const ref = useRef<T | null>(null)

  // Si el usuario pidió reducir movimiento, el contenido arranca visible:
  // diferir su aparición solo para animarla no tendría sentido si la
  // animación en sí no va a ocurrir. Se calcula al inicializar el estado
  // (no dentro de un efecto) para no disparar un set-state síncrono extra.
  const [visible, setVisible] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )

  useEffect(() => {
    if (visible) return

    const node = ref.current
    if (!node) return

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry?.isIntersecting) {
          setVisible(true)
          observer.unobserve(node)
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -100px 0px' },
    )

    observer.observe(node)
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { ref, visible }
}
