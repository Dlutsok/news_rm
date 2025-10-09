import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import {
  HiOutlineNewspaper,
  HiOutlineCog6Tooth,
  HiOutlineGlobeAlt,
  HiOutlineCurrencyDollar
} from 'react-icons/hi2'
import { useAuth } from '@contexts/AuthContext'

const Navigation = () => {
  const { isAdmin, isAnalyst } = useAuth()
  const router = useRouter()
  
  const canViewAnalytics = () => isAdmin() || isAnalyst()

  const navigationItems = [
    { id: 'monitoring', label: 'Мониторинг новостей', icon: HiOutlineNewspaper, href: '/monitoring' },
    { id: 'published', label: 'Опубликованные новости', icon: HiOutlineGlobeAlt, href: '/published' },
    ...(canViewAnalytics() ? [
      { id: 'expenses', label: 'Мониторинг расходов', icon: HiOutlineCurrencyDollar, href: '/expenses' },
    ] : []),
    ...(isAdmin() ? [
      { id: 'settings', label: 'Настройки', icon: HiOutlineCog6Tooth, href: '/settings' },
    ] : [])
  ]

  const isActivePath = (href) => {
    if (href === '/monitoring' && router.pathname === '/') {
      return true
    }
    return router.pathname === href
  }

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8" aria-label="Navigation">
        {navigationItems.map((item) => (
          <Link
            key={item.id}
            href={item.href}
            className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center transition-colors duration-200 ${
              isActivePath(item.href)
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {item.icon && <item.icon className="mr-2 w-4 h-4" />}
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  )
}

export default Navigation