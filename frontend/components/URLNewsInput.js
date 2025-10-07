import { useState } from 'react'
import { HiOutlineGlobeAlt, HiOutlineNewspaper, HiOutlineExclamationCircle, HiOutlinePlus, HiOutlineEye } from 'react-icons/hi2'
import { LuLoader2 } from 'react-icons/lu'
import Button from './ui/Button'
import Input from './ui/Input'
import Alert from './ui/Alert'
import ProjectSelectorModal from './ProjectSelectorModal'
import ArticlePreviewModal from './ArticlePreviewModal'
import apiClient from '@utils/api'

const URLNewsInput = ({ onArticleLoaded, onDraftGenerated, onGenerationStarted }) => {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [parsedArticle, setParsedArticle] = useState(null)
  const [isProjectSelectorOpen, setIsProjectSelectorOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  // Состояния для генерации
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationStep, setGenerationStep] = useState(null) // 'parsing', 'summary', 'article', 'image', 'done'
  const [generatedDraft, setGeneratedDraft] = useState(null)

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

    try {
      const result = await apiClient.parseURLArticle(url.trim())

      if (result.success) {
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
  }

  const handleAddToProject = () => {
    setIsProjectSelectorOpen(true)
  }

  const handleProjectSelected = async (projectData) => {
    setIsProjectSelectorOpen(false)
    setIsGenerating(true)
    setError(null)

    const projectName = projectData.type // 'gynecology.school', 'therapy.school', 'pediatrics.school'

    console.log('Generating article from URL:', {
      url: parsedArticle.url,
      project: projectName,
      projectData: projectData
    })

    // Уведомляем родительский компонент, что началась генерация
    if (onGenerationStarted) {
      onGenerationStarted(parsedArticle.id)
    }

    try {
      // Этап 1: Парсинг (уже выполнен, но показываем для UI)
      setGenerationStep('parsing')

      // Этап 2-4: Генерация через API (summary + article + image)
      setGenerationStep('summary')

      const result = await apiClient.generateFromURL(
        parsedArticle.url,
        projectName,
        true, // генерировать изображение
        null  // дефолтные опции форматирования
      )

      if (result.success) {
        setGenerationStep('done')
        setGeneratedDraft({
          draft_id: result.draft_id,
          source_url: result.source_url,
          source_domain: result.source_domain,
          news_text: result.news_text,
          seo_title: result.seo_title,
          seo_description: result.seo_description,
          seo_keywords: result.seo_keywords,
          image_url: result.image_url,
          project: projectName
        })

        // Уведомляем родительский компонент (monitoring.js) о новом черновике
        if (onDraftGenerated) {
          onDraftGenerated({
            id: result.draft_id,
            article: parsedArticle,
            draft: result,
            isNew: true,
            source: 'url'
          })
        }

        // Очищаем состояние генерации и сбрасываем форму для нового ввода
        setTimeout(() => {
          setGeneratedDraft(null)
          setGenerationStep(null)
          handleReset()
        }, 2000)

      } else {
        setError(result.error || 'Не удалось сгенерировать статью')
        setGenerationStep(null)
      }
    } catch (err) {
      console.error('Error generating article from URL:', err)
      setError(err.message || 'Ошибка при генерации статьи')
      setGenerationStep(null)
    } finally {
      setIsGenerating(false)
    }
  }

  // Вспомогательная функция для отображения шага генерации
  const getGenerationStepLabel = (step) => {
    const steps = {
      'parsing': 'Парсинг статьи...',
      'summary': 'Генерация summary и статьи...',
      'article': 'Генерация финального текста...',
      'image': 'Генерация изображения...',
      'done': 'Готово!'
    }
    return steps[step] || step
  }

  return (
    <>
      <ProjectSelectorModal
        isOpen={isProjectSelectorOpen}
        onClose={() => !isGenerating && setIsProjectSelectorOpen(false)}
        onSelectProject={handleProjectSelected}
        article={parsedArticle}
      />
      <ArticlePreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        article={parsedArticle}
      />
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
                Вставьте ссылку на любую новость из интернета. Мы извлечём текст и обработаем его.
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

            <Button
              onClick={handleLoadArticle}
              disabled={isLoading || !url.trim()}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <LuLoader2 className="animate-spin mr-2" />
                  Загрузка новости...
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
              Мы автоматически извлечём текст статьи, очистим от рекламы и лишних элементов.
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

          {/* Индикатор прогресса генерации */}
          {isGenerating && generationStep && (
            <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <LuLoader2 className="w-5 h-5 text-purple-600 animate-spin flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-purple-900">
                    {getGenerationStepLabel(generationStep)}
                  </p>
                  {generationStep !== 'done' && (
                    <p className="text-xs text-purple-700 mt-1">
                      Пожалуйста, подождите. Это может занять до 2-3 минут...
                    </p>
                  )}
                </div>
              </div>
              {/* Прогресс бар */}
              <div className="mt-3 w-full bg-purple-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all duration-500"
                  style={{
                    width: generationStep === 'parsing' ? '25%' :
                           generationStep === 'summary' ? '50%' :
                           generationStep === 'article' ? '75%' :
                           generationStep === 'image' ? '90%' :
                           generationStep === 'done' ? '100%' : '0%'
                  }}
                />
              </div>
            </div>
          )}

          {/* Сообщение об успехе */}
          {generatedDraft && generationStep === 'done' && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">
                    Статья успешно сгенерирована!
                  </p>
                  <p className="text-xs text-green-700 mt-1">
                    Черновик #{generatedDraft.draft_id} добавлен в список. Теперь вы можете отредактировать и опубликовать её.
                  </p>
                </div>
              </div>
            </div>
          )}

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
                  {isGenerating ? (
                    <>
                      <LuLoader2 className="animate-spin mr-2" />
                      Генерация...
                    </>
                  ) : (
                    <>
                      <HiOutlinePlus className="mr-2" />
                      Добавить в проект
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="text-xs text-purple-800">
              <strong>Следующий шаг:</strong> Нажмите "Добавить в проект", выберите платформу
              (Gynecology School / Therapy School / Pediatrics School), и система автоматически сгенерирует
              адаптированную медицинскую статью с SEO и изображением.
            </p>
          </div>
        </div>
      )}
    </div>
    </>
  )
}

export default URLNewsInput
