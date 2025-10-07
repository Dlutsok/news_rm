import Head from 'next/head'
import ProtectedRoute from '@components/ProtectedRoute'
import Layout from '@components/Layout'
import Navigation from '@components/Navigation'
import SystemMonitoringDashboard from '@components/monitoring/SystemMonitoringDashboard'
import { useAuth } from '@contexts/AuthContext'
import { useRouter } from 'next/router'
import { useEffect } from 'react'
import {
  ServerIcon
} from '../components/ui/icons'

function SystemMonitoringContent() {
  const { isAdmin, isAnalyst, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  // Проверка доступа к аналитике (админ или аналитик)
  const canViewAnalytics = isAdmin() || isAnalyst()

  useEffect(() => {
    // Ждем загрузки данных пользователя
    if (!isLoading && isAuthenticated) {
      if (!canViewAnalytics) {
        router.push('/')
      }
    }
  }, [isLoading, isAuthenticated, canViewAnalytics, router])

  // Показываем загрузку пока проверяем права
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Проверка прав доступа...</p>
        </div>
      </div>
    )
  }

  if (!canViewAnalytics) {
    return null
  }

  const headerRight = (
    <div className="flex items-center space-x-4">
      <div className="bg-gray-600 p-2 rounded-md">
        <ServerIcon className="text-white text-sm" />
      </div>
      <div className="text-right">
        <p className="text-sm font-medium text-gray-900">Статус системы</p>
        <p className="text-xs text-gray-500">Онлайн</p>
      </div>
    </div>
  )

  return (
    <>
      <Head>
        <title>Мониторинг системы - Rusmedical News AI</title>
        <meta name="description" content="Мониторинг производительности и состояния системы" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      <Layout
        title="Мониторинг системы"
        breadcrumbs={[{ label: 'Главная', href: '/' }, { label: 'Мониторинг системы' }]}
        headerRight={headerRight}
      >
        <Navigation />
        <SystemMonitoringDashboard />
      </Layout>
    </>
  )
}

export default function SystemMonitoringPage() {
  return (
    <ProtectedRoute>
      <SystemMonitoringContent />
    </ProtectedRoute>
  )
}