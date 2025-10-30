import { useState } from 'react'
import { HiOutlineGlobeAlt, HiOutlineNewspaper, HiOutlineExclamationCircle, HiOutlinePlus, HiOutlineEye } from 'react-icons/hi2'
import { LuLoader2 } from 'react-icons/lu'
import Button from './ui/Button'
import Input from './ui/Input'
import Alert from './ui/Alert'
import ProjectSelectorModal from './ProjectSelectorModal'
import ArticlePreviewModal from './ArticlePreviewModal'
import ProgressModal from './ProgressModal'
import SummaryConfirmation from './SummaryConfirmation'
import ArticleEditor from './ArticleEditor'
import ArticlePreview from './ArticlePreview'
import PublicationModal from './PublicationModal'
import apiClient from '@utils/api'

const URLNewsInput = ({ onArticleLoaded, onDraftGenerated, onGenerationStarted }) => {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(null) // 'fetching', 'cleaning', 'done'
  const [error, setError] = useState(null)
  const [parsedArticle, setParsedArticle] = useState(null)
  
  // Модальные окна
  const [isProjectSelectorOpen, setIsProjectSelectorOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  // 🎯 FLOW ГЕНЕРАЦИИ (как в FoundNews)
  const [selectedProject, setSelectedProject] = useState(null)
  const [currentStep, setCurrentStep] = useState('project') // 'project', 'summary', 'editing', 'preview'
  const [summaryData, setSummaryData] = useState(null)
  const [generatedArticle, setGeneratedArticle] = useState(null)
  const [draftId, setDraftId] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showProgressModal, setShowProgressModal] = useState(false)

  // Состояния для публикации
  const [publishModal, setPublishModal] = useState({ open: false, project: null, bitrixId: null, url: null })
  const [isPublicationModalOpen, setIsPublicationModalOpen] = useState(false)
  const [publicationData, setPublicationData] = useState(null)

  const isValidURL = (string) => {
    try {
      new URL(string)
      return true
    } catch (_) {
      return false
    }
  }

  const handleLoadArticle = async () => {
    setError(null)

    if (!url.trim()) {
      setError('Пожалуйста, введите URL')
      return
    }

    if (!isValidURL(url)) {
      setError('Пожалуйста, введите корректный URL (например: https://example.com/news/123)')
      return
    }

    setIsLoading(true)
    setLoadingStep('fetching')

    try {
      // Этап 1: Парсинг через Jina AI
      setLoadingStep('fetching')
      
      const result = await apiClient.parseURLArticle(url.trim())
      
      // Этап 2: AI очистка контента (происходит автоматически в backend)
      setLoadingStep('cleaning')

      if (result.success) {
        setLoadingStep('done')
        
        const article = {
          id: result.article_id,  // ID статьи в БД
          title: result.title || extractTitle(result.content),
          text: result.content,
          url: result.url,
          domain: result.domain,
          source: 'url',
          published_at: new Date().toISOString()
        }

        setParsedArticle(article)

        if (onArticleLoaded) {
          onArticleLoaded(article)
        }
      } else {
        setError(result.error || 'Не удалось загрузить новость')
      }
    } catch (err) {
      console.error('Error loading article from URL:', err)
      setError(err.message || 'Ошибка при загрузке новости')
    } finally {
      setIsLoading(false)
      setLoadingStep(null)
    }
  }

  const extractTitle = (markdown) => {
    // Ищем первый заголовок в markdown
    const titleMatch = markdown.match(/^#\s+(.+)$/m) || markdown.match(/^Title:\s*(.+)$/m)
    if (titleMatch) {
      return titleMatch[1].trim()
    }

    // Если нет заголовка, берем первые 100 символов
    const firstLine = markdown.split('\n').find(line => line.trim().length > 10)
    return firstLine ? firstLine.substring(0, 100) : 'Новость из URL'
  }

  const handleReset = () => {
    setParsedArticle(null)
    setUrl('')
    setError(null)
    resetGenerationState()
  }

  const handleAddToProject = () => {
    setIsProjectSelectorOpen(true)
  }

  // 🎯 ГЛАВНАЯ ФУНКЦИЯ: Как в FoundNews.js
  const handleProjectSelected = async (projectData) => {
    console.log('🚀 Starting generation flow for URL article:', projectData)
    setSelectedProject(projectData)
    setIsProjectSelectorOpen(false)
    setShowProgressModal(true)
    setCurrentStep('summary')
    setIsGenerating(true)

    // Уведомляем родительский компонент
    if (onGenerationStarted) {
      onGenerationStarted(parsedArticle.id)
    }

    try {
      // Шаг 1: Генерация summary (как в FoundNews)
      console.log('📝 Generating summary...')
      const summaryResponse = await apiClient.request('/api/news-generation/summarize', {
        method: 'POST',
        body: JSON.stringify({
          article_id: parsedArticle.id,
          project: projectData.type,
        }),
      })

      setSummaryData({ 
        summary: summaryResponse.summary, 
        facts: summaryResponse.facts || [] 
      })
      setDraftId(summaryResponse.draft_id)
      console.log('✅ Summary generated:', summaryResponse)

    } catch (err) {
      console.error('❌ Error generating summary:', err)
      setError(err.message || 'Ошибка при создании выжимки')
      alert('Ошибка при создании выжимки: ' + err.message)
      resetGenerationState()
    } finally {
      setIsGenerating(false)
    }
  }

  // Подтверждение summary → генерация статьи
  const handleSummaryConfirm = async (confirmedSummary) => {
    setIsGenerating(true)

    try {
      // ШАГ 1: Подтверждение выжимки (обновление статуса черновика)
      console.log('✅ Confirming summary...')
      await apiClient.request('/api/news-generation/confirm-summary', {
        method: 'POST',
        body: JSON.stringify({
          draft_id: draftId,
          summary: confirmedSummary.summary,
          facts: confirmedSummary.facts,
        }),
      })

      // Переходим к следующему шагу
      setCurrentStep('editing')
      setSummaryData(null)

      // ШАГ 2: Генерация полной статьи
      console.log('📰 Generating full article...')
      const articleResponse = await apiClient.request('/api/news-generation/generate-article', {
        method: 'POST',
        body: JSON.stringify({
          draft_id: draftId,
          formatting_options: confirmedSummary.formatting_options || {}
        }),
      })

      setGeneratedArticle(articleResponse)
      console.log('✅ Article generated:', articleResponse)

      // Уведомляем родительский компонент
      if (onDraftGenerated) {
        onDraftGenerated({
          id: draftId,
          article: parsedArticle,
          draft: articleResponse,
          isNew: true,
          source: 'url'
        })
      }

    } catch (err) {
      console.error('❌ Error generating article:', err)
      alert('Ошибка при генерации статьи: ' + err.message)
      resetGenerationState()
    } finally {
      setIsGenerating(false)
    }
  }

  // Регенерация summary
  const handleSummaryRegenerate = async () => {
    setIsGenerating(true)

    try {
      const summaryResponse = await apiClient.request('/api/news-generation/summarize', {
        method: 'POST',
        body: JSON.stringify({
          article_id: parsedArticle.id,
          project: selectedProject.type,
        }),
      })

      setSummaryData({ 
        summary: summaryResponse.summary, 
        facts: summaryResponse.facts || [] 
      })
      setDraftId(summaryResponse.draft_id)
    } catch (err) {
      console.error('Error regenerating summary:', err)
      alert('Ошибка при регенерации выжимки: ' + err.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // Сохранение черновика
  const handleArticleSave = async (articleData) => {
    try {
      const savedData = await apiClient.request(`/api/news-generation/drafts/${draftId}`, {
        method: 'PUT',
        body: JSON.stringify(articleData),
      })
      setGeneratedArticle(savedData)
      console.log('✅ Draft saved:', savedData)
      alert('Черновик сохранен!')
    } catch (err) {
      console.error('Error saving draft:', err)
      alert('Ошибка при сохранении: ' + err.message)
    }
  }

  // Открыть preview
  const handlePreview = () => {
    setCurrentStep('preview')
  }

  // Регенерация изображения
  const handleRegenerateImage = async () => {
    try {
      setIsGenerating(true)
      const response = await apiClient.request('/api/news-generation/regenerate-image', {
        method: 'POST',
        body: JSON.stringify({
          draft_id: draftId,
          new_prompt: null  // Backend использует существующий промпт из черновика
        })
      })
      
      setGeneratedArticle(prev => ({
        ...prev,
        image_url: response.image_url
      }))
      // Уведомление убрано - изображение обновляется автоматически
    } catch (err) {
      console.error('Error regenerating image:', err)
      alert('Ошибка при регенерации изображения: ' + err.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // Функция для открытия модального окна публикации
  const openPublicationModal = (articleData = null, projectOrCode = null) => {
    // Определяем код проекта: 'GS' | 'TS' | 'PS'
    let resolvedCode = null
    if (typeof projectOrCode === 'string') {
      resolvedCode = projectOrCode
    } else if (projectOrCode && typeof projectOrCode === 'object') {
      resolvedCode = projectOrCode.code || null
    } else if (selectedProject && selectedProject.code) {
      resolvedCode = selectedProject.code
    }

    if (!resolvedCode) {
      alert('Выберите проект для публикации')
      return
    }

    // Для GS/PS/TS открываем модальное окно планирования публикации
    setPublicationData({
      articleData,
      projectCode: resolvedCode,
      draftId
    })
    setIsPublicationModalOpen(true)
  }

  // Функция обработки публикации из модального окна
  const handlePublicationFromModal = async (publishData) => {
    try {
      setIsGenerating(true)

      // Перед самой публикацией сохраняем последние правки из редактора,
      // чтобы в Битрикс ушёл актуальный HTML-контент
      try {
        const dataToPersist = publicationData?.articleData || generatedArticle
        if (dataToPersist && publicationData?.draftId) {
          const saved = await apiClient.request(`/api/news-generation/drafts/${publicationData.draftId}`, {
            method: 'PUT',
            body: JSON.stringify(dataToPersist)
          })
          setGeneratedArticle(saved)
        }
      } catch (persistErr) {
        console.error('Ошибка при сохранении черновика перед публикацией:', persistErr)
        // Не прерываем публикацию, но уведомим пользователя
        alert('Не удалось сохранить последние изменения перед публикацией. Будет опубликована предыдущая версия.')
      }

      const endpoint = '/api/news-generation/publish'

      const response = await apiClient.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(publishData)
      })

      if (response.success) {
        if (publishData.mode === 'now') {
          // Показываем результат публикации
          setPublishModal({
            open: true,
            project: response.project,
            bitrixId: response.bitrix_id,
            url: response.url
          })
        } else {
          // Показываем сообщение об успешном планировании
          alert(`Публикация запланирована на ${new Date(publishData.scheduled_at).toLocaleString('ru-RU')}`)
        }

        // Сбрасываем состояние после успешной публикации
        resetGenerationState()
      } else {
        throw new Error(response.error || 'Ошибка публикации')
      }
    } catch (error) {
      console.error('Ошибка публикации:', error)
      alert(`Ошибка публикации: ${error.message}`)
    } finally {
      setIsGenerating(false)
      setIsPublicationModalOpen(false)
    }
  }

  // Сброс состояния
  const resetGenerationState = () => {
    setSelectedProject(null)
    setCurrentStep('project')
    setSummaryData(null)
    setGeneratedArticle(null)
    setDraftId(null)
    setIsGenerating(false)
    setShowProgressModal(false)
    // Не сбрасываем publishModal здесь - пользователь закроет его вручную
    setIsPublicationModalOpen(false)
    setPublicationData(null)
  }

  // Вспомогательная функция для отображения шага загрузки
  const getLoadingStepLabel = (step) => {
    const steps = {
      'fetching': 'Загрузка статьи...',
      'cleaning': '🧹 AI очистка контента (GPT-4o-mini)...',
      'done': 'Готово!'
    }
    return steps[step] || 'Обработка...'
  }

  return (
    <>
      {/* Project Selector Modal */}
      <ProjectSelectorModal
        isOpen={isProjectSelectorOpen}
        onClose={() => !isGenerating && setIsProjectSelectorOpen(false)}
        onSelectProject={handleProjectSelected}
        article={parsedArticle}
      />

      {/* Article Preview Modal */}
      <ArticlePreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        article={parsedArticle}
      />

      {/* 🎯 ГЕНЕРАЦИЯ FLOW: Progress Modal */}
      <ProgressModal
        isOpen={showProgressModal}
        onClose={() => !isGenerating && resetGenerationState()}
        currentStep={currentStep}
        isGenerating={isGenerating}
        selectedProject={selectedProject}
        articleTitle={parsedArticle?.title}
      />

      {/* 🎯 Summary Confirmation Modal */}
      {currentStep === 'summary' && summaryData && (
        <SummaryConfirmation
          isOpen={true}
          summary={summaryData.summary || summaryData}
          facts={summaryData.facts || []}
          onConfirm={handleSummaryConfirm}
          onRegenerate={handleSummaryRegenerate}
          onClose={resetGenerationState}
          isLoading={isGenerating}
        />
      )}

      {/* 🎯 Article Editor Modal */}
      {currentStep === 'editing' && generatedArticle && (
        <ArticleEditor
          isOpen={true}
          articleData={generatedArticle}
          onSave={handleArticleSave}
          onPreview={handlePreview}
          onRegenerateImage={handleRegenerateImage}
          onPublish={openPublicationModal}
          publishLabel="Опубликовать"
          onClose={resetGenerationState}
          isLoading={isGenerating}
          isPublishing={isGenerating}
        />
      )}

      {/* 🎯 Article Preview Modal */}
      {currentStep === 'preview' && generatedArticle && selectedProject && (
        <ArticlePreview
          isOpen={true}
          articleData={generatedArticle}
          project={selectedProject}
          onPublish={openPublicationModal}
          onClose={() => setCurrentStep('editing')}
          isLoading={isGenerating}
        />
      )}

      {/* Модальное окно публикации */}
      <PublicationModal
        isOpen={isPublicationModalOpen}
        onClose={() => setIsPublicationModalOpen(false)}
        draftId={publicationData?.draftId}
        projectCode={publicationData?.projectCode}
        onPublish={handlePublicationFromModal}
      />

      {/* ОСНОВНОЙ UI */}
      <div className="space-y-4">
        {!parsedArticle ? (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start space-x-3 mb-4">
              <HiOutlineGlobeAlt className="w-6 h-6 text-purple-600 mt-1" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  Загрузить новость по URL
                </h3>
                <p className="text-sm text-gray-600">
                  Вставьте ссылку на любую новость из интернета. Мы извлечём текст и обработаем его через GPT-4o-mini.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <Input
                type="url"
                placeholder="https://example.com/news/article-123"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleLoadArticle()
                  }
                }}
              />

              {error && (
                <Alert type="error" className="flex items-start">
                  <HiOutlineExclamationCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </Alert>
              )}

              {/* Индикатор прогресса загрузки */}
              {isLoading && loadingStep && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <LuLoader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
                    <p className="text-sm font-medium text-blue-900">
                      {getLoadingStepLabel(loadingStep)}
                    </p>
                  </div>
                  {loadingStep === 'cleaning' && (
                    <p className="text-xs text-blue-700 mt-1 ml-6">
                      Используем GPT-4o-mini для удаления навигации, рекламы, footer...
                    </p>
                  )}
                </div>
              )}

              <Button
                onClick={handleLoadArticle}
                disabled={isLoading || !url.trim()}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <LuLoader2 className="animate-spin mr-2" />
                    {getLoadingStepLabel(loadingStep)}
                  </>
                ) : (
                  <>
                    <HiOutlineGlobeAlt className="mr-2" />
                    Загрузить новость
                  </>
                )}
              </Button>
            </div>

            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs text-blue-800">
                <strong>Совет:</strong> Поддерживаются любые новостные сайты.
                Мы автоматически извлечём текст статьи, очистим от рекламы и лишних элементов через AI.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg border-2 border-purple-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start space-x-3 flex-1">
                <HiOutlineNewspaper className="w-6 h-6 text-purple-600 mt-1 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 break-words">
                    {parsedArticle.title}
                  </h3>
                  <div className="flex items-center text-sm text-gray-500 mb-3">
                    <HiOutlineGlobeAlt className="w-4 h-4 mr-1" />
                    <span className="break-all">{parsedArticle.domain}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="prose prose-sm max-w-none mb-4">
              <p className="text-gray-700 line-clamp-6">
                {parsedArticle.text.substring(0, 500)}...
              </p>
            </div>

            <div className="flex flex-col space-y-3 pt-4 border-t border-gray-200">
              <div className="flex items-center text-sm text-green-600">
                <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Новость успешно загружена ({parsedArticle.text.length} символов)</span>
              </div>

              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPreviewOpen(true)}
                  className="text-purple-600 border-purple-200 hover:bg-purple-50"
                >
                  <HiOutlineEye className="mr-2" />
                  Посмотреть полный текст
                </Button>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleReset}
                  >
                    Загрузить другую
                  </Button>

                  <Button
                    size="sm"
                    onClick={handleAddToProject}
                    disabled={isGenerating}
                    className="bg-purple-600 hover:bg-purple-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    <HiOutlinePlus className="mr-2" />
                    Добавить в проект
                  </Button>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
              <p className="text-xs text-purple-800">
                <strong>Следующий шаг:</strong> Нажмите "Добавить в проект", выберите платформу
                (Gynecology School / Therapy School / Pediatrics School), и система автоматически сгенерирует
                адаптированную медицинскую статью с SEO и изображением через тот же процесс что и обычные статьи.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Модальное окно результата публикации */}
      {publishModal.open && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl border border-gray-100">
            <div className="px-6 py-5 border-b bg-gradient-to-r from-green-50 to-emerald-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Статья опубликована</h3>
                  {publishModal.project && (
                    <p className="text-sm text-gray-600">Проект: {publishModal.project}</p>
                  )}
                </div>
              </div>
            </div>
            <div className="px-6 py-5 space-y-3">
              {publishModal.url ? (
                <div className="text-gray-800 text-sm break-all">
                  Ссылка на публикацию:
                  <div>
                    <a href={publishModal.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline">
                      {publishModal.url}
                    </a>
                  </div>
                </div>
              ) : (
                <p className="text-gray-700">Публикация прошла успешно.</p>
              )}
            </div>
            <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-end">
              <button
                onClick={() => {
                  setPublishModal({ open: false, project: null, bitrixId: null, url: null })
                  resetGenerationState()
                }}
                className="px-5 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default URLNewsInput