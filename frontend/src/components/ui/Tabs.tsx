import type { ReactNode } from 'react'
import './Tabs.css'

export interface TabItem {
  id: string
  label: string
}

interface TabsProps {
  items: TabItem[]
  activeId: string
  onChange: (id: string) => void
  children?: ReactNode
}

export function Tabs({ items, activeId, onChange, children }: TabsProps) {
  return (
    <div className="tabs">
      <div className="tabs__list" role="tablist">
        {items.map((item) => (
          <button
            key={item.id}
            role="tab"
            type="button"
            aria-selected={item.id === activeId}
            className="tabs__tab"
            data-active={item.id === activeId}
            onClick={() => onChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="tabs__panel">{children}</div>
    </div>
  )
}
