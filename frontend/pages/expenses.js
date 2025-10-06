import Head from 'next/head'
import ProtectedRoute from '@components/ProtectedRoute'
import Layout from '@components/Layout'
import Navigation from '@components/Navigation'
import ExpenseMonitoring from '@components/ExpenseMonitoring'
import { useAuth } from '@contexts/AuthContext'
import { useRouter } from 'next/router'
import { useEffect } from 'react'

function ExpensesContent() {
  const { isAdmin, isAnalyst } = useAuth()
  const router = useRouter()

  // Проверка доступа к аналитике (админ или аналитик)
  const canViewAnalytics = () => isAdmin() || isAnalyst()

  useEffect(() => {
    if (!canViewAnalytics()) {
      router.push('/')
    }
  }, [canViewAnalytics, router])

  if (!canViewAnalytics()) {
    return null
  }

  return (
    <>
      <Head>
        <title>Мониторинг расходов - Rusmedical News AI</title>
        <meta name="description" content="Мониторинг расходов на API и другие сервисы" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      <Layout
        title="Мониторинг расходов"
        breadcrumbs={[{ label: 'Главная', href: '/' }, { label: 'Мониторинг расходов' }]}
      >
        <Navigation />
        <ExpenseMonitoring />
      </Layout>
    </>
  )
}

export default function ExpensesPage() {
  return (
    <ProtectedRoute>
      <ExpensesContent />
    </ProtectedRoute>
  )
}