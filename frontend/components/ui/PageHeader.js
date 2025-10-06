import React from 'react'

const PageHeader = ({ title, description, actions = null, icon: Icon }) => {
  return (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-start">
          {Icon && (
            <div className="bg-gradient-to-r from-purple-500 to-blue-600 p-2 rounded-lg mr-3">
              <Icon className="text-white w-5 h-5" />
            </div>
          )}
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">{title}</h2>
            {description && (
              <p className="text-gray-600 mt-1">{description}</p>
            )}
          </div>
        </div>
        {actions && <div className="flex items-center space-x-2">{actions}</div>}
      </div>
    </div>
  )
}

export default PageHeader


