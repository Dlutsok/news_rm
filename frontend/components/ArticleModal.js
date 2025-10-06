import { useState, useEffect } from 'react'
import {
  XIcon,
  LoadingIcon,
  ExternalIcon,
  CalendarIcon,
  GlobalIcon,
  ClockIcon,
  ViewIcon
} from './ui/icons'

const ArticleModal = ({ article, isOpen, onClose }) => {
  const [fullContent, setFullContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isOpen && article) {
      fetchFullArticle()
    }
  }, [isOpen, article])

  const fetchFullArticle = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`/api/news/article?url=${encodeURIComponent(article.url)}`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setFullContent(data.content)
      } else {
        setError('Не удалось загрузить полный текст статьи')
      }
    } catch (error) {
      console.error('Error fetching full article:', error)
      setError('Ошибка при загрузке статьи: ' + error.message)
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
      
      // Для дат в ISO формате (например, 2025-07-02T10:01:50) показываем только дату
      if (dateString.includes('T') && dateString.includes(':')) {
        return date.toLocaleDateString('ru-RU', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      }
      
      // Если время 00:00, показываем только дату
      if (date.getHours() === 0 && date.getMinutes() === 0) {
        return date.toLocaleDateString('ru-RU', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      }
      
      // Иначе показываем дату и время
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      console.error('Error formatting date:', error)
      return 'Дата не указана'
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[9997]">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full h-[95vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 pr-8">
              {article?.title}
            </h2>
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
              <span className="flex items-center">
                <CalendarIcon className="mr-1" />
                {formatDate(article?.published_date)}
              </span>
              {article?.published_time && (
                <span className="flex items-center">
                  <ClockIcon className="mr-1" />
                  {article.published_time}
                </span>
              )}
              {article?.views_count && (
                <span className="flex items-center">
                  <ViewIcon className="mr-1" />
                  {article.views_count} просмотров
                </span>
              )}
              <span className="flex items-center">
                <GlobalIcon className="mr-1" />
                {article?.source_site}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full flex-shrink-0"
          >
            <XIcon className="text-gray-500" />
          </button>
        </div>

        {/* Content - с полной прокруткой */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <LoadingIcon className="animate-spin w-6 h-6 text-blue-600 mr-3" />
              <span className="text-gray-600">Загрузка полного текста статьи...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <div className="text-red-800">{error}</div>
              <div className="mt-2">
                <a
                  href={article?.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-red-600 hover:text-red-800"
                >
                  <ExternalIcon className="mr-1" />
                  Открыть на сайте источника
                </a>
              </div>
            </div>
          )}

          {!loading && !error && fullContent && (
            <div className="prose max-w-none">
              <div className="text-gray-800 leading-relaxed text-base article-full-content">
                {/* Разбиваем текст на абзацы и отображаем каждый в отдельном div */}
                {fullContent.split('\n').map((paragraph, index) => (
                  paragraph.trim() ? (
                    <p key={index} className="content-paragraph">
                      {paragraph.trim()}
                    </p>
                  ) : (
                    <br key={index} />
                  )
                ))}
              </div>
            </div>
          )}

        <style jsx>{`
          .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
          }
          
          .modal-content {
            background: white;
            border-radius: 8px;
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
            margin: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          }
          
          .content-paragraph {
            margin-bottom: 1rem;
            line-height: 1.6;
            text-align: justify;
            color: #374151;
          }
          
          .article-full-content,
          .article-preview-content {
            white-space: pre-line;
            word-wrap: break-word;
          }
          
          .article-full-content p,
          .article-preview-content p {
            margin-bottom: 1rem;
            line-height: 1.6;
          }
          
          .close-button {
            position: absolute;
            top: 15px;
            right: 15px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6b7280;
            z-index: 1001;
          }
          
          .close-button:hover {
            color: #374151;
          }
        `}</style>

          {!loading && !error && !fullContent && (
            <div className="text-center py-8">
              <div className="text-gray-600 mb-4">
                Полный текст статьи недоступен
              </div>
              <a
                href={article?.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <ExternalIcon className="mr-2" />
                Читать на сайте источника
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50 flex-shrink-0">
          <div className="text-sm text-gray-500">
            Источник: {article?.source_site}
          </div>
          <div className="flex space-x-3">
            <a
              href={article?.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <ExternalIcon className="mr-2" />
              Открыть оригинал
            </a>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ArticleModal