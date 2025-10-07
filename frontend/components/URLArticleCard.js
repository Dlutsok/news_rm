import { HiOutlineGlobeAlt, HiOutlinePlus, HiOutlineTrash, HiOutlineEye, HiOutlineCheckCircle } from 'react-icons/hi2'
import { LuLoader2 } from 'react-icons/lu'
import Button from './ui/Button'
import { useState } from 'react'
import ProjectSelectorModal from './ProjectSelectorModal'
import ArticlePreviewModal from './ArticlePreviewModal'
import apiClient from '@utils/api'

const URLArticleCard = ({ entry, onGenerationStart, onDraftGenerated, onDelete }) => {
  const { id, article, status, draft, isNew, timestamp } = entry
  const [isProjectSelectorOpen, setIsProjectSelectorOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)

  const handleAddToProject = () => {
    setIsProjectSelectorOpen(true)
  }

  const handleProjectSelected = async (projectData) => {
    setIsProjectSelectorOpen(false)
    setIsGenerating(true)
    setError(null)

    const projectName = projectData.type

    // Уведомляем родительский компонент, что началась генерация
    if (onGenerationStart) {
      onGenerationStart(article.id, projectData)
    }

    try {
      const result = await apiClient.generateFromURL(
        article.url,
        projectName,
        true, // генерировать изображение
        null  // дефолтные опции форматирования
      )

      if (result.success) {
        // Уведомляем родительский компонент о завершении генерации
        if (onDraftGenerated) {
          onDraftGenerated({
            article: article,
            draft: result,
            isNew: true
          })
        }
      } else {
        setError(result.error || 'Не удалось сгенерировать статью')
      }
    } catch (err) {
      console.error('Error generating article from URL:', err)
      setError(err.message || 'Ошибка при генерации статьи')
    } finally {
      setIsGenerating(false)
    }
  }

  const getStatusBadge = () => {
    switch (status) {
      case 'loaded':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <HiOutlineCheckCircle className="w-4 h-4 mr-1" />
            Загружено
          </span>
        )
      case 'generating':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <LuLoader2 className="w-4 h-4 mr-1 animate-spin" />
            Генерация...
          </span>
        )
      case 'generated':
        return (
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <HiOutlineCheckCircle className="w-4 h-4 mr-1" />
              Готово
            </span>
            {isNew && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 animate-pulse">
                NEW
              </span>
            )}
          </div>
        )
      default:
        return null
    }
  }

  const getTimestamp = () => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000) // разница в секундах

    if (diff < 60) return 'только что'
    if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`
    if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`
    return date.toLocaleDateString('ru-RU')
  }

  return (
    <>
      <ProjectSelectorModal
        isOpen={isProjectSelectorOpen}
        onClose={() => setIsProjectSelectorOpen(false)}
        onSelectProject={handleProjectSelected}
        article={article}
      />
      <ArticlePreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        article={article}
      />

      <div className="bg-white border-2 border-purple-200 rounded-lg p-4 hover:border-purple-300 transition-colors">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-3 mb-2">
              <HiOutlineGlobeAlt className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-gray-900 mb-1 break-words line-clamp-2">
                  {article.title}
                </h4>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="break-all">{article.domain}</span>
                  <span>•</span>
                  <span className="text-xs">{getTimestamp()}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 mt-3">
              {getStatusBadge()}
            </div>

            {/* Превью текста статьи */}
            {status === 'loaded' && (
              <p className="text-sm text-gray-600 mt-3 line-clamp-2">
                {article.text?.substring(0, 150)}...
              </p>
            )}

            {/* Информация о сгенерированном черновике */}
            {status === 'generated' && draft && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  <strong>Черновик #{draft.draft_id}</strong> готов к публикации
                </p>
                {draft.seo_title && (
                  <p className="text-xs text-green-700 mt-1 line-clamp-1">
                    {draft.seo_title}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Кнопки действий */}
          <div className="flex flex-col gap-2 flex-shrink-0">
            {status === 'loaded' && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsPreviewOpen(true)}
                  className="text-purple-600 border-purple-200 hover:bg-purple-50"
                >
                  <HiOutlineEye className="w-4 h-4 mr-1" />
                  Просмотр
                </Button>
                <Button
                  size="sm"
                  onClick={handleAddToProject}
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                >
                  <HiOutlinePlus className="w-4 h-4 mr-1" />
                  В проект
                </Button>
              </>
            )}

            {status === 'generating' && (
              <div className="text-center">
                <LuLoader2 className="w-6 h-6 text-purple-600 animate-spin mx-auto" />
                <p className="text-xs text-gray-500 mt-1">Подождите...</p>
              </div>
            )}

            {status === 'generated' && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsPreviewOpen(true)}
                  className="text-purple-600 border-purple-200 hover:bg-purple-50"
                >
                  <HiOutlineEye className="w-4 h-4 mr-1" />
                  Просмотр
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onDelete(id)}
                  className="text-red-600 border-red-200 hover:bg-red-50"
                >
                  <HiOutlineTrash className="w-4 h-4 mr-1" />
                  Удалить
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default URLArticleCard
