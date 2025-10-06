import { useState, useEffect } from 'react'
import { FaPlay } from 'react-icons/fa'
import {
  LoadingIcon,
  CalendarIcon,
  NewsIcon,
  ExternalIcon,
  FilterIcon,
  ClockIcon,
  ViewIcon,
  InfoIcon,
  GlobalIcon
} from './ui/icons'
import ArticleModal from './ArticleModal'

const NewsParser = ({ selectedPlatform }) => {
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(false)
  const [maxArticles, setMaxArticles] = useState(20)
  const [dateFilter, setDateFilter] = useState('')
  const [fastMode, setFastMode] = useState(false)
  const [combineResults, setCombineResults] = useState(true)
  const [selectedSources, setSelectedSources] = useState(['ria', 'medvestnik', 'aig', 'remedium', 'rbc_medical']) // Новое состояние для источников
  const [lastParsed, setLastParsed] = useState(null)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Доступные источники новостей
  const availableSources = [
    { value: 'ria', label: 'РИА Новости', description: 'Федеральное информационное агентство' },
    { value: 'medvestnik', label: 'Медвестник', description: 'Медицинские новости и исследования' },
    { value: 'aig', label: 'AIG Journal', description: 'Акушерство, гинекология и репродуктология' },
    { value: 'remedium', label: 'Remedium.ru', description: 'Медицинский портал для специалистов' },
    { value: 'rbc_medical', label: 'РБК Медицина', description: 'Медицинские новости РБК' }
  ]

  const parseNewsToDatabase = async () => {
    setLoading(true)
    try {
      // Используем новый API эндпоинт для сохранения в БД
      const requestBody = {
        sources: selectedSources,
        max_articles: maxArticles,
        fetch_full_content: !fastMode,
        date_filter: dateFilter || undefined
      }
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 минут
      
      const response = await fetch('/api/news/parse-to-db', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Показываем результат сохранения в БД
      const resultSummary = []
      if (data.summary) {
        resultSummary.push(`✅ Сохранено: ${data.summary.total_saved}`)
        resultSummary.push(`🔄 Дубли: ${data.summary.total_duplicates}`)
        if (data.summary.total_errors > 0) {
          resultSummary.push(`❌ Ошибки: ${data.summary.total_errors}`)
        }
      }
      
      setNews([{
        title: `Парсинг завершен: ${data.status}`,
        content: `Результат сохранения в PostgreSQL:\n\n${resultSummary.join('\n')}\n\nИсточники:\n${Object.entries(data.sources || {}).map(([source, stats]) => 
          `• ${source.toUpperCase()}: спарсено ${stats.parsed}, сохранено ${stats.saved}, дубли ${stats.duplicates}`
        ).join('\n')}`,
        url: '#',
        source_site: 'database',
        published_date: new Date().toISOString()
      }])
      
      setLastParsed(new Date())
    } catch (error) {
      console.error('Error parsing to database:', error)
      setNews([{
        title: 'Ошибка парсинга в БД',
        content: `Произошла ошибка при парсинге и сохранении в базу данных: ${error.message}`,
        url: '#',
        source_site: 'error',
        published_date: new Date().toISOString()
      }])
    } finally {
      setLoading(false)
    }
  }

  const parseNews = async () => {
    setLoading(true)
    try {
      // Используем выбранные источники
      const requestBody = {
        sources: selectedSources, // Используем выбранные источники
        max_articles: maxArticles,
        fetch_full_content: !fastMode,
        combine_results: combineResults,
        date_filter: dateFilter || undefined
      }
      
      // Динамический таймаут в зависимости от количества статей
      let timeoutMs = 300000 // 5 минут по умолчанию
      if (maxArticles > 100) {
        timeoutMs = 900000 // 15 минут для больших запросов
      } else if (maxArticles > 50) {
        timeoutMs = 600000 // 10 минут для средних запросов
      }
      
      console.log(`Запуск парсинга ${maxArticles} статей с таймаутом ${timeoutMs/60000} минут`)
      
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
      
      const response = await fetch('/api/news/parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      if (combineResults) {
        // Объединенные результаты
        setNews(data.articles || [])
      } else {
        // Результаты по источникам - объединяем для отображения
        const allArticles = []
        if (data.sources) {
          Object.values(data.sources).forEach(sourceArticles => {
            allArticles.push(...sourceArticles)
          })
        }
        setNews(allArticles)
      }
      
      setLastParsed(new Date().toISOString())
      console.log(`Парсинг завершен успешно. Получено статей: ${news.length || data.articles?.length || 0}`)
      
    } catch (error) {
      console.error('Error parsing news:', error)
      
      if (error.name === 'AbortError') {
        const timeoutMinutes = maxArticles > 100 ? 15 : maxArticles > 50 ? 10 : 5
        alert(`Превышено время ожидания (${timeoutMinutes} минут). 
        
Рекомендации:
• Уменьшите количество статей (попробуйте ${Math.floor(maxArticles/2)})
• Включите быстрый режим для ускорения
• Выберите один источник вместо всех
• Проверьте логи сервера - возможно парсинг продолжается`)
      } else if (error.message.includes('Failed to fetch')) {
        alert(`Ошибка соединения с сервером. 
        
Возможные причины:
• Сервер перегружен большим запросом
• Проблемы с сетью
• Сервер временно недоступен

Попробуйте уменьшить количество статей или повторить запрос позже.`)
      } else if (error.message.includes('Unexpected token')) {
        alert(`Ошибка при парсинге ответа сервера. 
        
Возможные причины:
• Сервер еще обрабатывает запрос
• Неполный ответ от сервера
• Проблемы с форматом данных

Проверьте логи сервера - парсинг может продолжаться в фоне.`)
      } else if (error.message.includes('HTTP 5')) {
        alert(`Ошибка сервера (${error.message}). 
        
Сервер может быть перегружен большим запросом. 
Попробуйте уменьшить количество статей или повторить позже.`)
      } else {
        alert(`Ошибка при парсинге новостей: ${error.message}
        
Если парсинг большого количества статей, проверьте логи сервера - 
процесс может продолжаться в фоне.`)
      }
    } finally {
      setLoading(false)
    }
  }

  const testParser = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/news/sources/test')
      const data = await response.json()
      
      if (data.status === 'success') {
        alert(`Парсер работает! Найдено статей: ${data.sample_titles.length}\n\nПримеры заголовков:\n${data.sample_titles.join('\n')}`)
      } else {
        alert(`Ошибка парсера: ${data.message}`)
      }
    } catch (error) {
      console.error('Error testing parser:', error)
      alert('Ошибка при тестировании парсера: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана'
    
    try {
      const date = new Date(dateString)
      
      // Проверяем, что дата валидна
      if (isNaN(date.getTime())) {
        return 'Дата не указана'
      }
      
      // Для дат в ISO формате (например, 2025-07-02T10:01:50) показываем дату и время
      if (dateString.includes('T') && dateString.includes(':')) {
        return date.toLocaleDateString('ru-RU', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      }
      
      // Если время 00:00, показываем только дату
      if (date.getHours() === 0 && date.getMinutes() === 0) {
        return date.toLocaleDateString('ru-RU', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      }
      
      // Иначе показываем дату и время
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      console.error('Error formatting date:', error)
      return 'Дата не указана'
    }
  }

  const openArticleModal = (article) => {
    setSelectedArticle(article)
    setIsModalOpen(true)
  }

  const closeArticleModal = () => {
    setIsModalOpen(false)
    setSelectedArticle(null)
  }

  return (
    <div className="space-y-6">
      {/* Информация о выбранной платформе */}
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          🔧 Парсинг новостей
        </h3>
        <p className="text-gray-600 mb-6">
          Автоматический сбор медицинских новостей из различных источников с сохранением в PostgreSQL
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <GlobalIcon className="inline mr-1" />
              Источник новостей
            </label>
            <select
              value={selectedSources.length === 1 ? selectedSources[0] : 'all'}
              onChange={(e) => {
                if (e.target.value === 'all') {
                  setSelectedSources(['ria', 'medvestnik', 'aig', 'remedium', 'rbc_medical'])
                } else {
                  setSelectedSources([e.target.value])
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Все источники</option>
              {availableSources.map(source => (
                <option key={source.value} value={source.value}>
                  {source.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {selectedSources.length === 1 
                ? availableSources.find(s => s.value === selectedSources[0])?.description
                : 'Парсинг из всех доступных источников'
              }
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Количество статей
            </label>
            <input
              type="number"
              min="1"
              max="200"
              value={maxArticles}
              onChange={(e) => setMaxArticles(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {maxArticles > 100 && (
              <p className="text-xs text-amber-600 mt-1">
                ⚠️ Большое количество статей может занять до 15 минут. Рекомендуется включить быстрый режим.
              </p>
            )}
            {maxArticles > 50 && maxArticles <= 100 && (
              <p className="text-xs text-amber-600 mt-1">
                ⚠️ Большое количество статей может занять до 10 минут. Рекомендуется включить быстрый режим.
              </p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Фильтр по дате
            </label>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все новости</option>
              <option value="today">Сегодня</option>
              <option value="week">За неделю</option>
              <option value="month">За месяц</option>
            </select>
          </div>
          
          <div className="flex items-end space-x-2">
            <button
              onClick={parseNews}
              disabled={loading}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <>
                  <LoadingIcon className="animate-spin mr-2" />
                  Парсинг...
                </>
              ) : (
                <>
                  <FaPlay className="mr-2" />
                  Парсить
                </>
              )}
            </button>
            
            <button
              onClick={parseNewsToDatabase}
              disabled={loading}
              className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <>
                  <LoadingIcon className="animate-spin mr-2" />
                  Сохранение...
                </>
              ) : (
                <>
                  <NewsIcon className="mr-2" />
                  В PostgreSQL
                </>
              )}
            </button>
          </div>
        </div>
        
        <div className="flex space-x-4 items-center">
          <button
            onClick={testParser}
            disabled={loading}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 disabled:opacity-50"
          >
            Тест парсера
          </button>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={fastMode}
              onChange={(e) => setFastMode(e.target.checked)}
              className="mr-2 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              Быстрый режим (без дат и полного контента)
            </span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={combineResults}
              onChange={(e) => setCombineResults(e.target.checked)}
              className="mr-2 w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              Объединить результаты из всех источников
            </span>
          </label>
          
          {lastParsed && (
            <div className="flex items-center text-sm text-gray-500">
              <CalendarIcon className="mr-2" />
              Последний парсинг: {formatDate(lastParsed)}
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {news && news.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Найденные новости ({news.length})
            </h3>
            <div className="mt-1 space-y-1">
              {selectedPlatform && (
                <p className="text-sm text-gray-600">
                  Отфильтровано для платформы: {selectedPlatform}
                </p>
              )}
              <p className="text-sm text-gray-600">
                <GlobalIcon className="inline mr-1" />
                Источники: {selectedSources.map(sourceValue => {
                  const source = availableSources.find(s => s.value === sourceValue)
                  return source ? source.label : sourceValue
                }).join(', ')}
              </p>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200">
            {news.map((article, index) => (
              <div key={index} className="p-6 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="text-base font-medium text-gray-900 mb-2">
                      {article.title}
                    </h4>
                    
                    <p className="text-gray-600 mb-3 line-clamp-3">
                      {article.content}
                    </p>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span className="flex items-center">
                        <CalendarIcon className="mr-1" />
                        {formatDate(article.published_date)}
                      </span>
                      
                      {article.published_time && (
                        <span className="flex items-center">
                          <ClockIcon className="mr-1" />
                          {article.published_time}
                        </span>
                      )}
                      
                      {article.views_count && (
                        <span className="flex items-center">
                          <ViewIcon className="mr-1" />
                          {article.views_count} просмотров
                        </span>
                      )}
                      
                      <span className="flex items-center">
                        <FilterIcon className="mr-1" />
                        {article.source_site}
                      </span>
                    </div>
                  </div>
                  
                  <div className="ml-4 flex-shrink-0 space-y-2">
                    <button
                      onClick={() => openArticleModal(article)}
                      className="w-full inline-flex items-center justify-center px-3 py-2 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100"
                    >
                      <InfoIcon className="mr-2" />
                      Подробнее
                    </button>
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full inline-flex items-center justify-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <ExternalIcon className="mr-2" />
                      Источник
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {(!news || news.length === 0) && !loading && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FilterIcon className="text-6xl text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Новости не найдены
          </h3>
          <p className="text-gray-600">
            Запустите парсинг, чтобы получить последние медицинские новости
          </p>
        </div>
      )}

      {/* Article Modal */}
      <ArticleModal
        article={selectedArticle}
        isOpen={isModalOpen}
        onClose={closeArticleModal}
      />
    </div>
  )
}

export default NewsParser