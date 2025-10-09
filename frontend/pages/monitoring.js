import { useState, useEffect } from 'react'
import Head from 'next/head'
import {
  HiOutlineNewspaper,
  HiOutlineMagnifyingGlass,
  HiOutlineBolt,
  HiOutlineClock,
  HiOutlineGlobeAlt,
  HiOutlineCheckCircle,
  HiOutlineXCircle,
  HiOutlineBuildingOffice2,
  HiOutlineBeaker,
  HiOutlineAcademicCap,
  HiOutlineChevronDown,
  HiOutlineChevronUp,
  HiOutlineHeart
} from 'react-icons/hi2'
import { LuLoader2 } from 'react-icons/lu'
import FoundNews from '@components/FoundNews'
import URLNewsInput from '@components/URLNewsInput'
import URLArticleCard from '@components/URLArticleCard'
import ProtectedRoute from '@components/ProtectedRoute'
import apiClient from '@utils/api'
import Card from '@components/ui/Card'
import Button from '@components/ui/Button'
import Input from '@components/ui/Input'
import Alert from '@components/ui/Alert'
import Layout from '@components/Layout'
import Navigation from '@components/Navigation'
import { useAuth } from '@contexts/AuthContext'

function MonitoringContent() {
  const { isAdmin } = useAuth()
  const [systemHealth, setSystemHealth] = useState(null)
  const [isMonitoringExpanded, setIsMonitoringExpanded] = useState(false)

  // Источник новостей: 'found' или 'url'
  const [newsSource, setNewsSource] = useState('found')
  const [urlArticles, setUrlArticles] = useState([]) // Список всех загруженных URL-статей

  const handleURLArticleLoaded = (article) => {
    // Добавляем загруженную статью в список сразу после парсинга
    const newEntry = {
      id: `url_${Date.now()}_${article.id}`,
      article: article,
      status: 'loaded', // loaded → generating → generated
      draft: null,
      timestamp: new Date().toISOString()
    }

    setUrlArticles(prev => [newEntry, ...prev])
    console.log('URL article loaded and added to list:', newEntry)
  }

  const handleURLDraftGenerated = (draftData) => {
    // Обновляем существующую запись в списке (меняем статус на 'generated')
    setUrlArticles(prev => prev.map(entry => {
      if (entry.article.id === draftData.article.id) {
        return {
          ...entry,
          status: 'generated',
          draft: draftData.draft,
          isNew: true
        }
      }
      return entry
    }))

    console.log('URL draft generated, updated article status:', draftData)
  }

  const handleDeleteURLArticle = (entryId) => {
    setUrlArticles(prev => prev.filter(entry => entry.id !== entryId))
  }

  const handleURLGenerationStarted = (articleId) => {
    // Обновляем статус на 'generating' когда начинается генерация
    setUrlArticles(prev => prev.map(entry => {
      if (entry.article.id === articleId) {
        return { ...entry, status: 'generating' }
      }
      return entry
    }))
  }
  
  // Состояние для управления парсингом
  const [selectedSources, setSelectedSources] = useState(['RIA'])
  const [articleCount, setArticleCount] = useState(50)
  const [maxScanAllCount, setMaxScanAllCount] = useState(1000)
  const [isScanning, setIsScanning] = useState(false)
  const [scanResults, setScanResults] = useState({})
  const [scanController, setScanController] = useState(null)

  useEffect(() => {
    checkSystemHealth()
    
    // Загружаем настройки из localStorage после монтирования
    const savedArticleCount = localStorage.getItem('articleCount')
    const savedMaxScanAllCount = localStorage.getItem('maxScanAllCount')
    
    if (savedArticleCount) {
      setArticleCount(parseInt(savedArticleCount) || 50)
    }
    if (savedMaxScanAllCount) {
      setMaxScanAllCount(parseInt(savedMaxScanAllCount) || 1000)
    }
  }, [])

  const checkSystemHealth = async () => {
    try {
      const data = await apiClient.healthCheck()
      setSystemHealth(data)
    } catch (error) {
      console.error('Error checking system health:', error)
      setSystemHealth({ status: 'error' })
    }
  }

  // Функции для управления парсингом
  const handleSourceToggle = (source) => {
    setSelectedSources(prev => 
      prev.includes(source) 
        ? prev.filter(s => s !== source)
        : [...prev, source]
    )
  }

  const startScanning = async (scanAll = false) => {
    if (selectedSources.length === 0) {
      alert('Выберите хотя бы один источник для сканирования')
      return
    }

    setIsScanning(true)
    setScanResults({})

    try {
      // Создаем контроллер для отмены запроса при необходимости
      const controller = new AbortController()
      setScanController(controller)
      
      // Динамический таймаут в зависимости от количества статей
      const articlesToScan = scanAll ? maxScanAllCount : articleCount
      const timeoutMinutes = Math.max(10, Math.ceil(articlesToScan / 10)) // Минимум 10 минут, +1 минута на каждые 10 статей
      const timeoutMs = timeoutMinutes * 60 * 1000
      
      console.log(`Установлен таймаут: ${timeoutMinutes} минут для ${articlesToScan} статей`)
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

      const result = await apiClient.request('/api/news/parse-with-batch-save', {
        method: 'POST',
        body: JSON.stringify({
          sources: selectedSources,
          max_articles: scanAll ? maxScanAllCount : articleCount,
          fetch_full_content: true,
          combine_results: false
        }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      // apiClient.request уже проверяет response.ok и выбрасывает ошибку при неудаче
      setScanResults(result.sources || {})

      let message = `Сканирование завершено!\n`
      message += `Всего сохранено: ${result.total_saved} новых статей\n`
      message += `Дубликатов: ${result.total_duplicates}\n`

      if (result.sources) {
        message += `\nПо источникам:\n`
        Object.entries(result.sources).forEach(([source, data]) => {
          message += `• ${source}: ${data.saved} новых, ${data.duplicates} дубликатов\n`
        })
      }

      alert(message)
    } catch (error) {
      console.error('Scanning error:', error)
      console.error('Error name:', error.name)
      console.error('Error message:', error.message)
      console.error('Error stack:', error.stack)
      
      if (error.name === 'AbortError') {
        const articlesToScan = scanAll ? maxScanAllCount : articleCount
        const timeoutMin = Math.max(10, Math.ceil(articlesToScan / 10))
        alert(`Сканирование отменено по таймауту (${timeoutMin} минут). Попробуйте уменьшить количество статей.`)
      } else if (error.message.includes('Failed to fetch')) {
        alert('Ошибка соединения с сервером. Проверьте, что backend запущен.')
      } else if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
        alert('Ошибка сети. Возможно, backend перестал отвечать во время обработки.')
      } else {
        alert(`Ошибка сканирования: ${error.message}`)
      }
    } finally {
      setIsScanning(false)
      setScanController(null)
    }
  }

  const cancelScanning = () => {
    if (scanController) {
      scanController.abort()
      setIsScanning(false)
      setScanController(null)
      alert('Сканирование отменено')
    }
  }

  const estimateTimeoutMinutes = (count) => Math.max(10, Math.ceil((count || 0) / 10))

  const StatusBadge = () => (
    <div className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center border ${
      systemHealth?.status === 'healthy'
        ? 'bg-gray-50 text-gray-700 border-gray-200'
        : 'bg-gray-100 text-gray-800 border-gray-300'
    }`}>
      {systemHealth?.status === 'healthy' ? (
        <>
          <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
          Система работает
        </>
      ) : (
        <>
          <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
          Ошибка системы
        </>
      )}
    </div>
  )

  return (
    <>
      <Head>
        <title>Мониторинг новостей - Rusmedical News AI</title>
        <meta name="description" content="Автоматический сбор и анализ новостей из ведущих медицинских источников" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      <Layout
        title="Мониторинг новостей"
        breadcrumbs={[{ label: 'Главная', href: '/' }, { label: 'Мониторинг новостей' }]}
        headerRight={<StatusBadge />}
      >
        <Navigation />
        
        <div className="space-y-4">
          {/* Панель управления парсингом - только для администраторов */}
          {isAdmin() && (
            <div className="bg-white border border-gray-300 rounded-lg p-6">
            {/* Заголовок секции */}
            <div className="mb-6">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setIsMonitoringExpanded(!isMonitoringExpanded)}
              >
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center mr-4">
                    <HiOutlineMagnifyingGlass className="text-gray-600 w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">
                      Мониторинг медицинских ресурсов
                    </h2>
                    <p className="text-gray-500 text-sm mt-1">
                      Автоматический сбор и анализ новостей из ведущих медицинских источников
                    </p>
                  </div>
                </div>
                <div className="ml-4">
                  {isMonitoringExpanded ? (
                    <HiOutlineChevronUp className="text-gray-400 w-5 h-5" />
                  ) : (
                    <HiOutlineChevronDown className="text-gray-400 w-5 h-5" />
                  )}
                </div>
              </div>
            </div>

            {/* Содержимое блока мониторинга */}
            {isMonitoringExpanded && (
              <>
                {/* Панель управления */}
                <div className="bg-gray-50 rounded-lg border border-gray-200 p-6 mb-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-6">
                    <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Выбрано источников</p>
                          <p className="text-xl sm:text-2xl font-semibold text-gray-900 mt-1">{selectedSources.length}</p>
                        </div>
                        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                          <HiOutlineGlobeAlt className="text-gray-600 w-4 h-4 sm:w-5 sm:h-5" />
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Количество статей</p>
                          <p className="text-xl sm:text-2xl font-semibold text-gray-900 mt-1">{articleCount}</p>
                        </div>
                        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                          <HiOutlineMagnifyingGlass className="text-gray-600 w-4 h-4 sm:w-5 sm:h-5" />
                        </div>
                      </div>
                    </div>
                    <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 sm:col-span-2 lg:col-span-1">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Ожидаемый таймаут</p>
                          <p className="text-xl sm:text-2xl font-semibold text-gray-900 mt-1">{estimateTimeoutMinutes(articleCount)} мин</p>
                        </div>
                        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                          <HiOutlineClock className="text-gray-600 w-4 h-4 sm:w-5 sm:h-5" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700">Количество статей:</label>
                        <Input
                          type="number"
                          value={articleCount}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 50
                            setArticleCount(value)
                            localStorage.setItem('articleCount', value.toString())
                          }}
                          className="w-full"
                          min={1}
                          max={1000}
                          disabled={isScanning}
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-semibold text-gray-700">Максимум для "все":</label>
                        <Input
                          type="number"
                          value={maxScanAllCount}
                          onChange={(e) => {
                            const value = parseInt(e.target.value) || 1000
                            setMaxScanAllCount(value)
                            localStorage.setItem('maxScanAllCount', value.toString())
                          }}
                          className="w-full"
                          min={100}
                          max={10000}
                          disabled={isScanning}
                        />
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3 sm:gap-3">
                      <Button
                        onClick={() => startScanning(false)}
                        disabled={isScanning || selectedSources.length === 0}
                        variant="primary"
                        icon={HiOutlineMagnifyingGlass}
                        loading={isScanning}
                        className="w-full sm:w-auto touch-target"
                      >
                        Сканировать
                      </Button>
                      <Button
                        onClick={() => startScanning(true)}
                        disabled={isScanning || selectedSources.length === 0}
                        variant="success"
                        icon={HiOutlineBolt}
                        loading={isScanning}
                        className="w-full sm:w-auto touch-target"
                      >
                        <span className="hidden sm:inline">Полное сканирование ({maxScanAllCount})</span>
                        <span className="sm:hidden">Полное ({maxScanAllCount})</span>
                      </Button>
                    </div>
                  </div>
                </div>
            
            {/* Источники новостей */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <HiOutlineGlobeAlt className="mr-3 text-gray-600 w-5 h-5" />
                Источники новостей
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {[
                  {
                    key: 'RIA',
                    name: 'РИА Новости',
                    domain: 'ria.ru',
                    description: 'Федеральное информационное агентство',
                    icon: HiOutlineNewspaper
                  },
                  {
                    key: 'MEDVESTNIK',
                    name: 'Медвестник',
                    domain: 'medvestnik.ru',
                    description: 'Медицинские новости и исследования',
                    icon: HiOutlineBuildingOffice2
                  },
                  {
                    key: 'AIG',
                    name: 'AIG Journal',
                    domain: 'aig-journal.ru',
                    description: 'Акушерство, гинекология и репродуктология',
                    icon: HiOutlineHeart
                  },
                  {
                    key: 'REMEDIUM',
                    name: 'Remedium',
                    domain: 'remedium.ru',
                    description: 'Медицинский портал для специалистов',
                    icon: HiOutlineBeaker
                  },
                  {
                    key: 'RBC_MEDICAL',
                    name: 'РБК Медицина',
                    domain: 'rbc.ru/medical',
                    description: 'Медицинские новости РБК',
                    icon: HiOutlineAcademicCap
                  }
                ].map((source) => (
                  <div
                    key={source.key}
                    className={`relative border rounded-lg p-4 cursor-pointer ${
                      selectedSources.includes(source.key)
                        ? 'border-gray-900 bg-gray-50'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                    onClick={() => handleSourceToggle(source.key)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedSources.includes(source.key)}
                          onChange={() => handleSourceToggle(source.key)}
                          className="mr-3 w-4 h-4 text-gray-900 border-gray-300 rounded"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center mr-3">
                          <source.icon className="text-gray-600 w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-900">{source.name}</h4>
                          <p className="text-xs text-gray-500">{source.domain}</p>
                        </div>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${
                        selectedSources.includes(source.key) ? 'bg-gray-900' : 'bg-gray-300'
                      }`}></div>
                    </div>

                    <p className="text-sm text-gray-600 mb-3">
                      {source.description}
                    </p>

                    <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      selectedSources.includes(source.key)
                        ? 'bg-gray-900 text-white'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      <div className={`w-2 h-2 rounded-full mr-1 ${
                        selectedSources.includes(source.key) ? 'bg-white' : 'bg-gray-400'
                      }`}></div>
                      {selectedSources.includes(source.key) ? 'Выбран' : 'Готов'}
                    </div>

                    {scanResults[source.key] && (
                      <div className="mt-3 p-3 bg-gray-100 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-gray-700 font-medium text-xs flex items-center">
                            <HiOutlineCheckCircle className="mr-2 text-gray-600 w-4 h-4" />
                            Найдено: {scanResults[source.key].saved}
                          </span>
                          {scanResults[source.key].duplicates > 0 && (
                            <span className="text-gray-500 text-xs">
                              ({scanResults[source.key].duplicates} дубликатов)
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Статус сканирования */}
            {isScanning && (
              <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-gray-700">
                    <LuLoader2 className="animate-spin mr-3 w-5 h-5" />
                    <span className="font-medium">
                      Сканирование в процессе... Выбранные источники: {selectedSources.join(', ')}
                    </span>
                  </div>
                  <Button
                    variant="error"
                    size="sm"
                    onClick={cancelScanning}
                  >
                    Отменить
                  </Button>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  Ожидаемое время выполнения: {estimateTimeoutMinutes(articleCount)} минут
                </div>
              </div>
            )}
              </>
            )}
            </div>
          )}

          {/* Переключатель источника новостей */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-semibold text-gray-700">Источник новостей:</span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setNewsSource('found')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                    newsSource === 'found'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <HiOutlineNewspaper className="inline-block mr-2 w-4 h-4" />
                  Найденные новости
                </button>
                <button
                  onClick={() => setNewsSource('url')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                    newsSource === 'url'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <HiOutlineGlobeAlt className="inline-block mr-2 w-4 h-4" />
                  Добавить по URL
                </button>
              </div>
            </div>
          </div>

          {/* Контент в зависимости от источника */}
          {newsSource === 'found' ? (
            /* Найденные новости из базы данных */
            <FoundNews />
          ) : (
            /* Добавление новости по URL */
            <div className="space-y-6">
              {/* Форма загрузки URL */}
              <URLNewsInput
                onArticleLoaded={handleURLArticleLoaded}
                onDraftGenerated={handleURLDraftGenerated}
                onGenerationStarted={handleURLGenerationStarted}
              />

              {/* Список загруженных URL-статей */}
              {urlArticles.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Загруженные статьи ({urlArticles.length})
                    </h3>
                    {urlArticles.some(entry => entry.isNew) && (
                      <span className="text-sm text-purple-600 font-medium animate-pulse">
                        Есть новые статьи!
                      </span>
                    )}
                  </div>

                  <div className="space-y-3">
                    {urlArticles.map(entry => (
                      <URLArticleCard
                        key={entry.id}
                        entry={entry}
                        onGenerationStart={handleURLGenerationStarted}
                        onDraftGenerated={handleURLDraftGenerated}
                        onDelete={handleDeleteURLArticle}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Layout>
    </>
  )
}

export default function MonitoringPage() {
  return (
    <ProtectedRoute>
      <MonitoringContent />
    </ProtectedRoute>
  )
}