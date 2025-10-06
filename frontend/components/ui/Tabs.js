import React from 'react'

const Tabs = ({ tabs = [], activeId, onChange }) => {
  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange && onChange(tab.id)}
            className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center transition-colors duration-200 ${
              activeId === tab.id
                ? 'border-corporate-500 text-corporate-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.icon && <tab.icon className="mr-2 w-4 h-4" />}
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

export default Tabs


