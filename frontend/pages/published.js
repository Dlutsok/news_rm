import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import { useAuth } from '@contexts/AuthContext'
import { formatWithTimezone, TimeDisplay } from '@utils/timezone'
import Layout from '@components/Layout'
import Navigation from '@components/Navigation'
import ProtectedRoute from '@components/ProtectedRoute'
import TelegramPostManager from '@components/TelegramPostManager'
import ArticleEditor from '@components/ArticleEditor'

const PublishedNewsContent = () => {
  const { user } = useAuth()
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({
    project: '',
    status: '',
    author: '',
    date_from: '',
    date_to: '',
    page: 1,
    limit: 20
  })
  const [pagination, setPagination] = useState({
    total: 0,
    pages: 0,
    page: 1
  })
  const [telegramModal, setTelegramModal] = useState({
    isOpen: false,
    newsId: null,
    newsData: null
  })
  const [editModal, setEditModal] = useState({
    isOpen: false,
    draftId: null,
    draftData: null
  })

  const fetchPublishedNews = async () => {
    try {
      setLoading(true)
      setError('')

      const params = new URLSearchParams()
      Object.keys(filters).forEach(key => {
        if (filters[key]) {
          params.append(key, filters[key])
        }
      })

      const response = await fetch(`/api/proxy/news-generation/published?${params.toString()}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Ошибка при загрузке данных')
      }

      const data = await response.json()
      setNews(data.items || [])
      setPagination({
        total: data.total || 0,
        pages: data.pages || 0,
        page: data.page || 1
      })

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPublishedNews()
  }, [filters])

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: key !== 'page' ? 1 : value
    }))
  }

  const formatDateTime = (dateString) => {
    return formatWithTimezone(dateString)
  }


  const handleTelegramPosts = (draft) => {
    setTelegramModal({
      isOpen: true,
      newsId: draft.id,
      newsData: {
        id: draft.id,
        seo_title: draft.seo_title,
        title: draft.seo_title,
        news_text: draft.news_text,
        image_url: draft.image_url,
        generated_image_url: draft.generated_image_url,
        project: draft.project,
        published_url: draft.published_url || `https://site.com/news/${draft.id}` // Заглушка для URL
      }
    })
  }

  const closeTelegramPosts = () => {
    setTelegramModal({
      isOpen: false,
      newsId: null,
      newsData: null
    })
  }

  const getStatusBadge = (status) => {
    const badges = {
      scheduled: {
        color: 'bg-yellow-100 text-yellow-800',
        text: 'Запланировано'
      },
      published: {
        color: 'bg-green-100 text-green-800',
        text: 'Опубликовано'
      }
    }

    const badge = badges[status] || { color: 'bg-gray-100 text-gray-800', text: status }
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.text}
      </span>
    )
  }

  const getProjectBadges = (item) => {
    const projectColors = {
      'GS': { color: 'bg-pink-100 text-pink-800', text: 'GS' },
      'TS': { color: 'bg-blue-100 text-blue-800', text: 'TS' },
      'PS': { color: 'bg-purple-100 text-purple-800', text: 'PS' },
      'TEST': { color: 'bg-yellow-100 text-yellow-800', text: 'TEST' },
      'TEST2': { color: 'bg-orange-100 text-orange-800', text: 'TEST2' },
    }

    // Если есть множественные публикации, отображаем их
    if (item.published_projects && item.published_projects.length > 0) {
      return (
        <div className="flex flex-wrap gap-1">
          {item.published_projects.map((pub, index) => {
            const badge = projectColors[pub.project_code] || { color: 'bg-gray-100 text-gray-800', text: pub.project_code }
            return (
              <span
                key={index}
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}
                title={`${pub.project_name} (ID: ${pub.bitrix_id})`}
              >
                {badge.text}
              </span>
            )
          })}
        </div>
      )
    }

    // Фолбэк на старое поле для обратной совместимости
    if (item.published_project_code) {
      const badge = projectColors[item.published_project_code] || { color: 'bg-gray-100 text-gray-800', text: item.published_project_code }
      return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
          {badge.text}
        </span>
      )
    }

    // Если нет информации о публикации
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        -
      </span>
    )
  }

  const reschedulePublication = async (draftId, newTime) => {
    try {
      // Получаем CSRF токен
      const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/)
      const csrf = match ? decodeURIComponent(match[1]) : null
      
      const headers = {
        'Content-Type': 'application/json'
      }
      
      if (csrf) {
        headers['X-CSRF-Token'] = csrf
        headers['x-csrf-token'] = csrf
      }
      
      const response = await fetch('/api/news-generation/schedule', {
        method: 'PATCH',
        headers,
        credentials: 'include',
        body: JSON.stringify({
          draft_id: draftId,
          scheduled_at: newTime
        })
      })

      if (!response.ok) {
        throw new Error('Ошибка при изменении времени')
      }

      await fetchPublishedNews()
    } catch (err) {
      alert(`Ошибка: ${err.message}`)
    }
  }

  const cancelPublication = async (draftId) => {
    if (!confirm('Отменить публикацию?')) return

    try {
      // Получаем CSRF токен
      const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/)
      const csrf = match ? decodeURIComponent(match[1]) : null

      const headers = {
        'Content-Type': 'application/json'
      }

      if (csrf) {
        headers['X-CSRF-Token'] = csrf
        headers['x-csrf-token'] = csrf
      }

      const response = await fetch(`/api/news-generation/schedule/${draftId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers
      })

      if (!response.ok) {
        throw new Error('Ошибка при отмене публикации')
      }

      await fetchPublishedNews()
    } catch (err) {
      alert(`Ошибка: ${err.message}`)
    }
  }

  // Функция для открытия редактора для запланированной статьи
  const handleEditScheduled = async (draftId) => {
    try {
      const response = await fetch(`/api/proxy/news/draft/${draftId}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Ошибка при получении данных черновика')
      }

      const draftData = await response.json()
      setEditModal({
        isOpen: true,
        draftId: draftId,
        draftData: draftData
      })
    } catch (err) {
      alert(`Ошибка: ${err.message}`)
    }
  }

  // Функция для регенерации изображения в редакторе запланированной статьи
  const handleRegenerateImageInEditor = async (newPrompt) => {
    try {
      const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/)
      const csrf = match ? decodeURIComponent(match[1]) : null

      const headers = {
        'Content-Type': 'application/json'
      }

      if (csrf) {
        headers['X-CSRF-Token'] = csrf
        headers['x-csrf-token'] = csrf
      }

      const response = await fetch('/api/news-generation/regenerate-image', {
        method: 'POST',
        credentials: 'include',
        headers: headers,
        body: JSON.stringify({
          draft_id: editModal.draftId,
          new_prompt: newPrompt || null  // null = использовать существующий промпт из summary
        })
      })

      if (!response.ok) {
        throw new Error(`Ошибка ${response.status}`)
      }

      const data = await response.json()

      // Обновляем данные в editModal
      setEditModal(prev => ({
        ...prev,
        draftData: {
          ...prev.draftData,
          image_url: data.image_url,
          generated_image_url: data.image_url,
          image_prompt: data.prompt || prev.draftData.image_prompt
        }
      }))

      console.log('Изображение успешно перегенерировано')
    } catch (err) {
      console.error('Error regenerating image:', err)
      alert(`Ошибка при регенерации изображения: ${err.message}`)
      throw err
    }
  }

  // Функция для сохранения изменений в редакторе
  const handleSaveEdit = async (updatedData) => {
    try {
      const match = document.cookie.match(/(?:^|; )csrf_token=([^;]+)/)
      const csrf = match ? decodeURIComponent(match[1]) : null

      const headers = {
        'Content-Type': 'application/json'
      }

      if (csrf) {
        headers['X-CSRF-Token'] = csrf
        headers['x-csrf-token'] = csrf
      }

      // Структура данных для ArticleDraftUpdate
      const updatePayload = {
        news_text: updatedData.news_text || '',
        seo_title: updatedData.seo_title || '',
        seo_description: updatedData.seo_description || '',
        seo_keywords: updatedData.seo_keywords || [],
        image_prompt: updatedData.image_prompt || '',
        image_url: updatedData.image_url || ''
      }

      const response = await fetch(`/api/news-generation/drafts/${editModal.draftId}`, {
        method: 'PUT',
        credentials: 'include',
        headers,
        body: JSON.stringify(updatePayload)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Ошибка при сохранении изменений')
      }

      setEditModal({ isOpen: false, draftId: null, draftData: null })
      await fetchPublishedNews()
    } catch (err) {
      alert(`Ошибка: ${err.message}`)
    }
  }

  return (
    <>
      <Head>
        <title>Опубликованные новости - Rusmedical News AI</title>
        <meta name="description" content="Управление опубликованными и запланированными новостями" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      <Layout
        title="Опубликованные новости"
        breadcrumbs={[{ label: 'Главная', href: '/' }, { label: 'Опубликованные новости' }]}
      >
        <Navigation />
        
        <div className="space-y-4">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Опубликованные новости</h2>
        <p className="mt-1 text-gray-600">
          Управление опубликованными и запланированными новостями
        </p>
      </div>

      {/* Фильтры */}
      <div className="bg-white border border-gray-200 rounded mb-4">
        <div className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Проект
              </label>
              <select
                value={filters.project}
                onChange={(e) => handleFilterChange('project', e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 touch-target"
              >
                <option value="">Все проекты</option>
                <option value="gynecology.school">Gynecology School</option>
                <option value="therapy.school">Therapy School</option>
                <option value="pediatrics.school">Pediatrics School</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Статус
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 touch-target"
              >
                <option value="">Все статусы</option>
                <option value="scheduled">Запланировано</option>
                <option value="published">Опубликовано</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Дата от
              </label>
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => handleFilterChange('date_from', e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 touch-target"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Дата до
              </label>
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => handleFilterChange('date_to', e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 touch-target"
              />
            </div>
          </div>
          
          <div className="mt-3 flex justify-between items-center text-sm">
            <button
              onClick={() => {
                setFilters({
                  project: '',
                  status: '',
                  author: '',
                  date_from: '',
                  date_to: '',
                  page: 1,
                  limit: 20
                })
              }}
              className="text-gray-600 hover:text-gray-900"
            >
              Сбросить фильтры
            </button>

            <p className="text-gray-500">
              Найдено: {pagination.total} записей
            </p>
          </div>
        </div>
      </div>

      {/* Таблица */}
      <div className="bg-white border border-gray-200 rounded">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Загрузка...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchPublishedNews}
              className="mt-2 text-blue-600 hover:text-blue-800"
            >
              Попробовать снова
            </button>
          </div>
        ) : news.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-600">Новостей не найдено</p>
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto table-mobile sm:table-tablet md:table-md">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Проект
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Заголовок
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Автор
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Статус
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Дата и время
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {news.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        {getProjectBadges(item)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-2">
                          <div className="text-sm font-medium text-gray-900 max-w-md">
                            {item.title}
                          </div>
                          {/* Действия под заголовком */}
                          <div className="flex flex-col sm:flex-row flex-wrap gap-2">
                            {item.status === 'scheduled' && (
                              <>
                                <button
                                  onClick={() => handleEditScheduled(item.id)}
                                  className="inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded touch-target w-full sm:w-auto"
                                >
                                  Изменить
                                </button>
                                <button
                                  onClick={() => cancelPublication(item.id)}
                                  className="inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded touch-target w-full sm:w-auto"
                                >
                                  Отменить
                                </button>
                              </>
                            )}
                            {item.status === 'published' && (
                              <>
                                <button
                                  onClick={() => handleTelegramPosts(item)}
                                  className="inline-flex items-center justify-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded touch-target w-full sm:w-auto"
                                  title="Создать Telegram пост"
                                >
                                  <svg className="w-4 h-4 mr-1" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                                  </svg>
                                  Telegram
                                </button>
                                {item.bitrix_id && (
                                  <span className="inline-flex items-center justify-center px-3 py-2 text-sm text-green-600 bg-green-50 rounded font-medium w-full sm:w-auto">
                                    ID: {item.bitrix_id}
                                  </span>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {item.author_name}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {getStatusBadge(item.status)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        <div className="space-y-1">
                          {item.status === 'scheduled' ? (
                            <>
                              <div className="font-medium text-yellow-600">
                                <TimeDisplay
                                  isoString={item.scheduled_at}
                                  showRelative={true}
                                  showUTC={true}
                                />
                              </div>
                              <div className="text-xs text-gray-400">
                                Создано: <TimeDisplay isoString={item.created_at} />
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="font-medium">
                                <TimeDisplay
                                  isoString={item.published_at}
                                  showUTC={true}
                                />
                              </div>
                              <div className="text-xs text-gray-400">
                                Создано: <TimeDisplay isoString={item.created_at} />
                              </div>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Пагинация */}
            {pagination.pages > 1 && (
              <div className="bg-white px-3 sm:px-4 py-3 flex items-center justify-between border-t border-gray-200">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => handleFilterChange('page', Math.max(1, pagination.page - 1))}
                    disabled={pagination.page <= 1}
                    className="relative inline-flex items-center px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 touch-target"
                  >
                    Предыдущая
                  </button>
                  <span className="flex items-center text-sm text-gray-500">
                    {pagination.page} из {pagination.pages}
                  </span>
                  <button
                    onClick={() => handleFilterChange('page', Math.min(pagination.pages, pagination.page + 1))}
                    disabled={pagination.page >= pagination.pages}
                    className="relative inline-flex items-center px-4 py-3 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 touch-target"
                  >
                    Следующая
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Показано{' '}
                      <span className="font-medium">
                        {Math.min((pagination.page - 1) * filters.limit + 1, pagination.total)}
                      </span>{' '}
                      до{' '}
                      <span className="font-medium">
                        {Math.min(pagination.page * filters.limit, pagination.total)}
                      </span>{' '}
                      из{' '}
                      <span className="font-medium">{pagination.total}</span>{' '}
                      результатов
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      {Array.from({ length: pagination.pages }, (_, i) => i + 1).map(page => (
                        <button
                          key={page}
                          onClick={() => handleFilterChange('page', page)}
                          className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                            page === pagination.page
                              ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
        </div>


        {/* Telegram Posts Modal */}
        <TelegramPostManager
          newsId={telegramModal.newsId}
          newsData={telegramModal.newsData}
          isOpen={telegramModal.isOpen}
          onClose={closeTelegramPosts}
        />

        {/* Article Editor Modal for Scheduled Articles */}
        {editModal.isOpen && editModal.draftData && (
          <ArticleEditor
            isOpen={editModal.isOpen}
            onClose={() => setEditModal({ isOpen: false, draftId: null, draftData: null })}
            articleData={editModal.draftData}
            onSave={handleSaveEdit}
            onRegenerateImage={handleRegenerateImageInEditor}
            publishLabel="Сохранить изменения"
          />
        )}
      </Layout>
    </>
  )
}

export default function PublishedPage() {
  return (
    <ProtectedRoute>
      <PublishedNewsContent />
    </ProtectedRoute>
  )
}