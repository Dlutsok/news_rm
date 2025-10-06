import React, { useEffect, useState } from 'react'
import UserInfo from './UserInfo'
import apiClient from '@utils/api'

const Breadcrumbs = ({ items = [] }) => {
  if (!items.length) return null
  return (
    <nav className="text-xs sm:text-sm text-gray-500" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-1 sm:space-x-2 overflow-x-auto">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-center flex-shrink-0">
            {idx > 0 && <span className="mx-1 sm:mx-2 text-gray-300">/</span>}
            {item.href ? (
              <a href={item.href} className="hover:text-gray-700 truncate max-w-[120px] sm:max-w-none">{item.label}</a>
            ) : (
              <span className="text-gray-700 truncate max-w-[120px] sm:max-w-none">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

const Layout = ({ title = 'Rusmedical News AI', breadcrumbs = [], headerRight = null, children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex justify-between items-center py-3 sm:py-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center">
                <div className="mr-2 sm:mr-3 flex-shrink-0">
                  <img
                    src="/favicon.svg"
                    alt="Logo"
                    className="w-6 h-6 sm:w-8 sm:h-8"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <h1 className="text-base sm:text-lg md:text-xl font-semibold text-gray-900 truncate">{title}</h1>
                </div>
              </div>
              <div className="mt-1 sm:mt-2">
                <Breadcrumbs items={breadcrumbs} />
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4 flex-shrink-0 ml-3">
              {headerRight && (
                <div className="hidden sm:block">
                  {headerRight}
                </div>
              )}
              <UserInfo />
            </div>
          </div>
          {/* Мобильная версия headerRight */}
          {headerRight && (
            <div className="pb-3 sm:hidden border-t border-gray-100 pt-3">
              {headerRight}
            </div>
          )}
        </div>
      </header>

      {/* Main content container */}
      <main className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8">
        {children}
      </main>
    </div>
  )
}

export default Layout


