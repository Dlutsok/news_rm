import { useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import ProtectedRoute from '@components/ProtectedRoute'
import Layout from '@components/Layout'
import Navigation from '@components/Navigation'

function HomeContent() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to monitoring page as the main functionality
    router.push('/monitoring')
  }, [router])

  return (
    <>
      <Head>
        <title>Rusmedical News AI</title>
        <meta name="description" content="ИИ-сервис автоматизации новостных материалов для медицинских платформ" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      <Layout
        title="Rusmedical News AI"
        breadcrumbs={[{ label: 'Главная' }]}
      >
        <Navigation />
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Перенаправление...</p>
          </div>
        </div>
      </Layout>
    </>
  )
}

export default function Home() {
  return (
    <ProtectedRoute>
      <HomeContent />
    </ProtectedRoute>
  )
}