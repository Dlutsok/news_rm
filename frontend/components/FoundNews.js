import { useState, useEffect } from 'react'
import {
  NewsIcon,
  CalendarIcon,
  ExternalIcon,
  FilterIcon,
  ClockIcon,
  ViewIcon,
  InfoIcon,
  GlobalIcon,
  XIcon,
  LoadingIcon,
  RefreshIcon,
  PlusIcon,
  DatabaseIcon,
  UserIcon,
  WarningIcon,
  CheckIcon,
  SaveIcon,
  DeleteIcon
} from './ui/icons'
import ProjectSelector from './ProjectSelector'
import ProjectSelectorModal from './ProjectSelectorModal'
// Bitrix публикация отключена
import SummaryConfirmation from './SummaryConfirmation'
import ArticleEditor from './ArticleEditor'
import ArticlePreview from './ArticlePreview'
import ProgressModal from './ProgressModal'
import PublicationModal from './PublicationModal'
import DraftRecoveryPanel from './DraftRecoveryPanel'
import DraftSavedNotification from './DraftSavedNotification'
import Button from './ui/Button'
import Badge from './ui/Badge'
import Card from './ui/Card'
import Input from './ui/Input'
import NewsStatusBadge from './NewsStatusBadge'
import apiClient from '@utils/api'

const FoundNews = ({ selectedPlatform }) => {
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedSource, setSelectedSource] = useState('ria') // По умолчанию ria.ru
  const [limit, setLimit] = useState(100)
  const [offset, setOffset] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isProjectSelectorOpen, setIsProjectSelectorOpen] = useState(false)
  const [articleToAdd, setArticleToAdd] = useState(null)

  // Новые состояния для генерации новостей
  const [selectedProject, setSelectedProject] = useState(null)
  const [currentStep, setCurrentStep] = useState('project') // project, summary, editing, preview
  const [summaryData, setSummaryData] = useState(null)
  const [generatedArticle, setGeneratedArticle] = useState(null)
  const [draftId, setDraftId] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showProgressModal, setShowProgressModal] = useState(false)
  // Для совместимости со старой логикой селектора Bitrix
  const [selectedBitrixProject, setSelectedBitrixProject] = useState(null)
  const [showBitrixProjectSelector, setShowBitrixProjectSelector] = useState(false)
  // Модальное окно успешной публикации
  const [publishModal, setPublishModal] = useState({ open: false, project: null, bitrixId: null, url: null })
  
  // Состояние для нового модального окна публикации
  const [isPublicationModalOpen, setIsPublicationModalOpen] = useState(false)
  const [publicationData, setPublicationData] = useState(null)

  // Состояния для системы восстановления черновиков
  const [draftErrorNotification, setDraftErrorNotification] = useState(null)
  const [showDraftRecovery, setShowDraftRecovery] = useState(true)

  // Публикация отключена

  // Доступные источники новостей
  const availableSources = [
    { value: 'ria', label: 'РИА Новости', description: 'Федеральное информационное агентство' },
    { value: 'medvestnik', label: 'Медвестник', description: 'Медицинские новости и исследования' },
    { value: 'aig', label: 'AIG Journal', description: 'Акушерство, гинекология и репродуктология' },
    { value: 'remedium', label: 'Remedium.ru', description: 'Медицинский портал для специалистов' },
    { value: 'rbc_medical', label: 'РБК Медицина', description: 'Медицинские новости РБК' }
  ]

  // Загрузка новостей при изменении источника или при первой загрузке
  useEffect(() => {
    loadNewsFromDatabase()
  }, [selectedSource, limit, offset])

  const loadNewsFromDatabase = async () => {
    setLoading(true)
    try {
      const data = await apiClient.request(`/api/news/articles-with-publication-status?source=${selectedSource}&limit=${limit}&offset=${offset}`)
      setNews(data)
      setLastUpdated(new Date())
      console.log(`Loaded ${data.length} articles from ${selectedSource}`)
    } catch (error) {
      console.error('Error loading news from database:', error)
      setNews([])
    } finally {
      setLoading(false)
    }
  }

  const handleSourceChange = (source) => {
    setSelectedSource(source)
    setOffset(0) // Сбрасываем пагинацию при смене источника
  }

  const handleRefresh = () => {
    loadNewsFromDatabase()
  }

  const currentPage = Math.floor(offset / limit) + 1
  const canPrev = offset > 0
  const canNext = news.length >= limit
  const goPrev = () => setOffset(prev => Math.max(0, prev - limit))
  const goNext = () => setOffset(prev => prev + limit)

  // Фильтры/поиск/сортировка
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all') // all | published | scheduled | draft
  const [dateFrom, setDateFrom] = useState('') // yyyy-mm-dd
  const [dateTo, setDateTo] = useState('')
  const [sortBy, setSortBy] = useState('date_desc') // date_desc | date_asc | views_desc | views_asc

  const normalizeDate = (value) => {
    if (!value) return null
    try {
      const d = new Date(value)
      if (isNaN(d.getTime())) return null
      return d
    } catch {
      return null
    }
  }

  const filteredNews = (news || [])
    .filter((a) => {
      // Статус публикации
      if (statusFilter === 'published' && !a.is_published) return false
      if (statusFilter === 'scheduled' && !a.is_scheduled) return false
      if (statusFilter === 'draft' && !a.has_draft) return false
      return true
    })
    .filter((a) => {
      // Поиск по заголовку/контенту
      if (!searchQuery.trim()) return true
      const q = searchQuery.toLowerCase()
      const title = (a.title || '').toLowerCase()
      const content = (a.content || '').toLowerCase()
      return title.includes(q) || content.includes(q)
    })
    .filter((a) => {
      // Диапазон дат
      const from = dateFrom ? normalizeDate(dateFrom + 'T00:00:00') : null
      const to = dateTo ? normalizeDate(dateTo + 'T23:59:59') : null
      const dateStr = a.published_date || a.created_at
      const d = normalizeDate(dateStr)
      if (!d) return true
      if (from && d < from) return false
      if (to && d > to) return false
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'views_desc') return (b.views_count || 0) - (a.views_count || 0)
      if (sortBy === 'views_asc') return (a.views_count || 0) - (b.views_count || 0)
      // Дата
      const da = normalizeDate(a.published_date || a.created_at)?.getTime() || 0
      const db = normalizeDate(b.published_date || b.created_at)?.getTime() || 0
      if (sortBy === 'date_asc') return da - db
      return db - da // date_desc по умолчанию
    })

  const openArticleModal = (article) => {
    setSelectedArticle(article)
    setIsModalOpen(true)
  }

  const closeArticleModal = () => {
    setSelectedArticle(null)
    setIsModalOpen(false)
  }

  const openProjectSelector = (article) => {
    setArticleToAdd(article)
    setIsProjectSelectorOpen(true)
  }

  const closeProjectSelector = () => {
    setArticleToAdd(null)
    setIsProjectSelectorOpen(false)
  }

  const handleProjectSelect = async (project, article) => {
    console.log('Добавляем статью в проект:', project.name, article.title)
    setSelectedProject(project)
    setArticleToAdd(article)
    setIsProjectSelectorOpen(false)
    setShowProgressModal(true)

    // Сначала проверяем, есть ли уже существующий черновик для этой статьи и проекта
    const existingDraft = await checkExistingDraft(article.id, project.type)

    if (existingDraft) {
      console.log('Найден существующий черновик:', existingDraft.id)
      // Загружаем существующий черновик
      setDraftId(existingDraft.id)
      setCurrentStep('editing')

      // Проверяем статус черновика
      if ((existingDraft.status === 'generated' || existingDraft.status === 'scheduled' || existingDraft.status === 'published') && existingDraft.generated_news_text) {
        // Черновик готов, переходим к редактированию
        setGeneratedArticle({
          news_text: existingDraft.generated_news_text,
          seo_title: existingDraft.generated_seo_title,
          seo_description: existingDraft.generated_seo_description,
          seo_keywords: existingDraft.generated_seo_keywords ? JSON.parse(existingDraft.generated_seo_keywords) : [],
          image_prompt: existingDraft.generated_image_prompt,
          image_url: existingDraft.generated_image_url,
          draft_id: existingDraft.id
        })
      } else if (existingDraft.status === 'summary_confirmed' && existingDraft.summary) {
        // Выжимка подтверждена, можем сразу перейти к генерации статьи
        setCurrentStep('editing')
        setSummaryData({
          summary: existingDraft.summary,
          facts: existingDraft.facts ? JSON.parse(existingDraft.facts) : []
        })

        // Начинаем генерацию статьи
        try {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 минут timeout

          const data = await apiClient.request('/api/news-generation/generate-article', {
            method: 'POST',
            body: JSON.stringify({
              draft_id: existingDraft.id,
              formatting_options: {}
            }),
            signal: controller.signal,
          })
          clearTimeout(timeoutId)
          setGeneratedArticle(data)
        } catch (error) {
          console.error('Ошибка при генерации статьи:', error)
          setCurrentStep('summary')
        }
      } else if (existingDraft.summary) {
        // Есть выжимка, показываем её для подтверждения
        setCurrentStep('summary')
        setSummaryData({
          summary: existingDraft.summary,
          facts: existingDraft.facts ? JSON.parse(existingDraft.facts) : []
        })
      } else {
        // Черновик пустой, начинаем сначала
        setCurrentStep('summary')
        await startArticleSummarization(project, article)
      }
    } else {
      // Черновика нет, создаём новый
      setCurrentStep('summary')
      await startArticleSummarization(project, article)
    }
  }

  // Функция для проверки существующего черновика
  const checkExistingDraft = async (articleId, projectType) => {
    try {
      const response = await apiClient.request(`/api/news-generation/drafts/by-article/${articleId}?project=${projectType}`)
      return response
    } catch (error) {
      console.log('Черновик не найден или произошла ошибка:', error)
      return null
    }
  }

  // Функция для сжатия статьи с помощью GPT-5 (на бэке используется gpt-5-mini)
  const startArticleSummarization = async (project, article) => {
    setIsGenerating(true)
    setCurrentStep('summary')
    
    try {
      const data = await apiClient.request('/api/news-generation/summarize', {
        method: 'POST',
        body: JSON.stringify({
          article_id: article.id,
          project: project.type,
        }),
      })
      setSummaryData({ summary: data.summary, facts: data.facts || [] })
      setDraftId(data.draft_id)
      console.log('Сжатие статьи завершено:', data)

      // Учёт расходов перенесён на бэкенд
    } catch (error) {
      console.error('Ошибка при сжатии статьи:', error)

      // Показываем уведомление о сохранении черновика
      setDraftErrorNotification({
        draftId: draftId,
        errorMessage: error.message,
        errorStep: 'summary',
        onRetry: (retryDraftId) => retryDraftOperation(retryDraftId),
        onDismiss: () => setDraftErrorNotification(null)
      })

      alert('Ошибка при сжатии статьи: ' + error.message)
      resetGenerationState()
    } finally {
      setIsGenerating(false)
    }
  }

  // Подтверждение сжатия и переход к генерации полной статьи
  const handleSummaryConfirm = async (confirmedSummary) => {
    setIsGenerating(true)
    
    try {
      // Сначала подтверждаем сжатие
      await apiClient.request('/api/news-generation/confirm-summary', {
        method: 'POST',
        body: JSON.stringify({
          draft_id: draftId,
          summary: confirmedSummary.summary,
          facts: confirmedSummary.facts,
        }),
      })

      // Переходим к следующему шагу (это закроет окно подтверждения)
      setCurrentStep('editing')
      setSummaryData(null)

      // Затем генерируем полную статью (с увеличенным timeout для изображений)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 минут timeout
      
      try {
        const data = await apiClient.request('/api/news-generation/generate-article', {
          method: 'POST',
          body: JSON.stringify({
            draft_id: draftId,
            formatting_options: confirmedSummary.formatting_options
          }),
          signal: controller.signal,
        })
        clearTimeout(timeoutId)
        console.log('Генерация статьи завершена:', data)
        console.log('Структура данных:', Object.keys(data))
        setGeneratedArticle(data)
      } catch (fetchError) {
        clearTimeout(timeoutId)
        
        if (fetchError.name === 'AbortError') {
          console.error('Timeout при генерации статьи')

          // Показываем уведомление о сохранении черновика для timeout
          setDraftErrorNotification({
            draftId: draftId,
            errorMessage: 'Генерация статьи заняла слишком много времени',
            errorStep: 'generation',
            onRetry: (retryDraftId) => retryDraftOperation(retryDraftId),
            onDismiss: () => setDraftErrorNotification(null)
          })

          alert('Генерация статьи заняла слишком много времени. Попробуйте еще раз или отключите генерацию изображений.')
        } else {
          console.error('Ошибка при генерации статьи:', fetchError)

          // Показываем уведомление о сохранении черновика
          setDraftErrorNotification({
            draftId: draftId,
            errorMessage: fetchError.message,
            errorStep: 'generation',
            onRetry: (retryDraftId) => retryDraftOperation(retryDraftId),
            onDismiss: () => setDraftErrorNotification(null)
          })

          alert('Ошибка при генерации статьи: ' + fetchError.message)
        }
        // Возвращаемся к шагу выбора проекта при ошибке
        setCurrentStep('project')
        setSummaryData(null)
      }
    } catch (error) {
      console.error('Общая ошибка при генерации статьи:', error)
      alert('Ошибка при генерации статьи: ' + error.message)
      // Возвращаемся к шагу выбора проекта при ошибке
      setCurrentStep('project')
      setSummaryData(null)
    } finally {
      setIsGenerating(false)
    }
  }

  // Повторная генерация сжатия
  const handleSummaryRegenerate = async () => {
    await startArticleSummarization(selectedProject, articleToAdd)
  }

  // Сохранение отредактированной статьи
  const handleArticleSave = async (editedArticle) => {
    setIsGenerating(true)
    
    try {
      const data = await apiClient.request(`/api/news-generation/drafts/${draftId}`, {
        method: 'PUT',
        body: JSON.stringify(editedArticle),
      })
      setGeneratedArticle(data)
      console.log('Статья сохранена:', data)
    } catch (error) {
      console.error('Ошибка при сохранении статьи:', error)
      alert('Ошибка при сохранении статьи: ' + error.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // Переход к предпросмотру
  const handlePreview = () => {
    setCurrentStep('preview')
  }

  // Перегенерация изображения
  const handleRegenerateImage = async (newPrompt) => {
    setIsGenerating(true)
    
    try {
      const data = await apiClient.request('/api/news-generation/regenerate-image', {
        method: 'POST',
        body: JSON.stringify({
          draft_id: draftId,
          new_prompt: newPrompt,
        }),
      })
      setGeneratedArticle(prev => ({
        ...prev,
        image_url: data.image_url,
        image_prompt: newPrompt,
      }))
      console.log('Изображение перегенерировано:', data)
      // Учёт расходов перенесён на бэкенд
    } catch (error) {
      console.error('Ошибка при перегенерации изображения:', error)
      alert('Ошибка при перегенерации изображения: ' + error.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // Публикация: используем ранее выбранный проект
  // Функция принимает данные статьи (если есть) и объект проекта или его код
  // Новая функция для открытия модального окна публикации
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

  // Оставляем старую функцию для обратной совместимости  
  const openBitrixProjectSelector = openPublicationModal

  // Публикация статьи в выбранный проект Bitrix
  const handlePublish = async (articleData = null, projectCode = null) => {
    console.log('🚀 Debug handlePublish:')
    console.log('articleData:', !!articleData)
    console.log('projectCode (переданный):', projectCode)
    // Используем переданный проект или выбранный ранее через модалку проектов
    const targetProject = projectCode || selectedBitrixProject || selectedProject?.code
    console.log('targetProject (итоговый):', targetProject)
    
    if (!targetProject) {
      console.log('❌ ОШИБКА: Нет проекта для публикации!')
      alert('Выберите проект для публикации')
      return
    }
    
    console.log('✅ Продолжаем публикацию в проект:', targetProject)
    
    setIsGenerating(true)
    
    try {
      console.log('Публикуем статью в проект:', targetProject)
      console.log('Draft ID:', draftId)
      
      // Если переданы данные статьи из редактора, сначала сохраняем их
      if (articleData) {
        console.log('Сохраняем изменения перед публикацией...')
        const savedData = await apiClient.request(`/api/news-generation/drafts/${draftId}`, {
          method: 'PUT',
          body: JSON.stringify(articleData),
        })
        setGeneratedArticle(savedData)
      }
      
      // Определяем main_type на основе проекта
      let mainType = null;
      if (targetProject === 'GS') {
        mainType = 1; // ID для "Женское здоровье"
      } else if (targetProject === 'TS') {
        mainType = 2; // ID для "Терапия"
      } else if (targetProject === 'PS') {
        mainType = 3; // ID для "Педиатрия"
      }
      
      const data = await apiClient.request('/api/news-generation/publish-to-bitrix', {
        method: 'POST',
        body: JSON.stringify({
          draft_id: draftId,
          project_code: targetProject,
          main_type: mainType,
        }),
      })

      if (data.success) {
        console.log('Статья успешно опубликована:', data)
        setPublishModal({ open: true, project: data.project, bitrixId: data.bitrix_id, url: data.url || null })
        
        // Обновляем список новостей, чтобы показать статус публикации
        await loadNewsFromDatabase()
        
        resetGenerationState()
      } else {
        console.error('Ошибка при публикации статьи:', data)
        alert('Ошибка при публикации статьи: ' + (data.detail || data.error || 'Неизвестная ошибка'))
      }
    } catch (error) {
      console.error('Ошибка при публикации статьи:', error)
      alert('Ошибка при публикации статьи: ' + error.message)
    } finally {
      setIsGenerating(false)
      setShowBitrixProjectSelector(false)
    }
  }


  // Функция для восстановления черновика после ошибки
  const retryDraftOperation = async (retryDraftId) => {
    try {
      setIsGenerating(true)
      const response = await apiClient.request(`/api/news-generation/retry/${retryDraftId}`, {
        method: 'POST'
      })

      if (response.success) {
        // Перезагружаем черновик и продолжаем с того места, где остановились
        const draftData = await apiClient.request(`/api/news-generation/drafts/${retryDraftId}`)
        setDraftId(retryDraftId)
        setGeneratedArticle(draftData)
        setCurrentStep('editing')
        setDraftErrorNotification(null)
        alert('Черновик успешно восстановлен!')
      }
    } catch (error) {
      console.error('Ошибка при восстановлении черновика:', error)
      alert('Ошибка при восстановлении черновика: ' + error.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // Обработчик для восстановления черновика из панели восстановления
  const handleDraftRecovered = (draftId, recoveredData) => {
    setDraftId(draftId)
    setGeneratedArticle(recoveredData)
    setCurrentStep('editing')
    alert(`Черновик #${draftId} успешно восстановлен!`)
  }

  // Сброс состояния генерации
  const resetGenerationState = () => {
    setSelectedProject(null)
    setCurrentStep('project')
    setSummaryData(null)
    setGeneratedArticle(null)
    setDraftId(null)
    setIsGenerating(false)
    setArticleToAdd(null)
    setShowProgressModal(false)
    setSelectedBitrixProject(null)
    setShowBitrixProjectSelector(false)
    setDraftErrorNotification(null)
  }

  // Функция для удаления черновика
  const handleDeleteDraft = async (article) => {
    if (!article.draft_id) {
      alert('У этой статьи нет черновика для удаления')
      return
    }

    if (!confirm('Вы уверены, что хотите удалить черновик? Это действие нельзя отменить.')) {
      return
    }

    try {
      const response = await apiClient.request(`/api/news-generation/drafts/${article.draft_id}`, {
        method: 'DELETE'
      })

      if (response.success) {
        alert('Черновик успешно удален')
        // Можно добавить логику обновления списка новостей здесь
        // Например, перезагрузить страницу или вызвать callback от родительского компонента
        window.location.reload()
      } else {
        throw new Error(response.message || 'Ошибка при удалении черновика')
      }
    } catch (error) {
      console.error('Error deleting draft:', error)
      alert(`Ошибка при удалении черновика: ${error.message}`)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана'
    
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (error) {
      return 'Некорректная дата'
    }
  }

  const getSourceColor = (source) => {
    const colors = {
      'ria': 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border border-blue-300',
      'medvestnik': 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300',
      'aig': 'bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800 border border-purple-300',
      'remedium': 'bg-gradient-to-r from-red-100 to-red-200 text-red-800 border border-red-300',
      'rbc_medical': 'bg-gradient-to-r from-orange-100 to-orange-200 text-orange-800 border border-orange-300'
    }
    return colors[source] || 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border border-gray-300'
  }

  const selectedSourceData = availableSources.find(s => s.value === selectedSource)

  return (
    <div className="space-y-6">
      {/* Панель восстановления черновиков */}
      {/* ВРЕМЕННО СКРЫТО
      {showDraftRecovery && (
        <DraftRecoveryPanel onDraftRecovered={handleDraftRecovered} />
      )}
      */}

      {/* Заголовок и управление */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <NewsIcon className="text-white w-5 h-5" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Найденные новости из БД
              </h2>
              <p className="text-gray-600 mt-1">
                Управление и обработка новостей из базы данных для проекта {selectedPlatform}
              </p>
            </div>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={loading}
            variant="primary"
            icon={RefreshIcon}
            loading={loading}
          >
            Обновить
          </Button>
        </div>

        {/* Выбор источника */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="flex items-center mb-4">
            <FilterIcon className="text-blue-600 mr-2 w-4 h-4" />
            <label className="text-lg font-semibold text-gray-900">
              Выбор источника новостей
            </label>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {availableSources.map((source) => (
              <button
                key={source.value}
                onClick={() => handleSourceChange(source.value)}
                className={`group p-3 sm:p-4 rounded-xl border-2 text-left transition-all duration-200 hover:shadow-md touch-target ${
                  selectedSource === source.value
                    ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 text-blue-700 shadow-md'
                    : 'border-gray-200 hover:border-blue-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-semibold text-xs sm:text-sm">{source.label}</div>
                  {selectedSource === source.value && (
                    <div className="w-3 h-3 bg-blue-500 rounded-full flex-shrink-0"></div>
                  )}
                </div>
                <div className="text-xs text-gray-600 leading-relaxed">{source.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Информация о выбранном источнике */}
        {selectedSourceData && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                  <GlobalIcon className="text-white w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{selectedSourceData.label}</h3>
                  <p className="text-sm text-gray-600">{selectedSourceData.description}</p>
                  {lastUpdated && (
                    <p className="text-xs text-gray-500 mt-1">
                      Последнее обновление: {formatDate(lastUpdated)}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center space-x-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{news.length}</div>
                  <div className="text-xs text-gray-500">Найдено статей</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-amber-600">{currentPage}</div>
                  <div className="text-xs text-gray-500">Страница</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <label className="block text-xs font-medium text-gray-700 mb-2">Показать статей:</label>
                  <select
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value))}
                    className="text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={200}>200</option>
                    <option value={500}>500</option>
                    <option value={1000}>1000</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

        {/* Панель фильтров */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Фильтры и сортировка</h3>
              <p className="text-sm text-gray-500">Уточните список с помощью поиска, статуса и диапазона дат</p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => { setSearchQuery(''); setStatusFilter('all'); setDateFrom(''); setDateTo(''); setSortBy('date_desc'); }}
            >
              Сбросить
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4">
            <div className="sm:col-span-2 lg:col-span-3 xl:col-span-2">
              <Input
                label="Поиск по заголовку/контенту"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Введите текст..."
                className="touch-target"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Статус публикации</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-corporate-500 focus:border-transparent touch-target"
              >
                <option value="all">Все</option>
                <option value="published">Опубликованные</option>
                <option value="scheduled">Запланированные</option>
                <option value="draft">Черновики</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">С даты</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-corporate-500 focus:border-transparent touch-target"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">По дату</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-corporate-500 focus:border-transparent touch-target"
              />
            </div>
            <div className="sm:col-span-2 lg:col-span-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">Сортировка</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-corporate-500 focus:border-transparent touch-target"
              >
                <option value="date_desc">По дате (новые → старые)</option>
                <option value="date_asc">По дате (старые → новые)</option>
                <option value="views_desc">По просмотрам (больше → меньше)</option>
                <option value="views_asc">По просмотрам (меньше → больше)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Список новостей */}
        {loading ? (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-purple-200 rounded-full animate-pulse"></div>
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-purple-600 rounded-full animate-spin border-t-transparent"></div>
            </div>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-3">
            Загрузка новостей...
          </h3>
          <p className="text-gray-600 mb-2">
            Получаем новости из источника <span className="font-medium text-purple-600">{selectedSourceData?.label}</span>
          </p>
          <div className="mt-4">
            <div className="w-32 h-1 bg-gray-200 rounded-full mx-auto overflow-hidden">
              <div className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
       ) : news && news.length > 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <NewsIcon className="text-white w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    Список новостей
                  </h3>
                  <p className="text-sm text-gray-600">
                    Найдено {news.length} статей из источника {selectedSourceData?.label}
                    {filteredNews.length !== news.length && (
                      <span className="ml-2 text-gray-500">• Отфильтровано: {filteredNews.length}</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`px-4 py-2 rounded-full text-sm font-semibold shadow-sm ${getSourceColor(selectedSource)}`}>
                  {selectedSourceData?.label}
                </span>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">{filteredNews.length}</div>
                  <div className="text-xs text-gray-500">статей</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-6 space-y-4">
            {filteredNews.map((article, index) => (
              <div key={article.id || index} className="group rounded-xl p-4 sm:p-6 transition-all duration-200 hover:shadow-md border bg-white hover:bg-gray-50 border-gray-100 hover:border-gray-200">
                <div className="flex flex-col lg:flex-row lg:justify-between lg:items-start space-y-4 lg:space-y-0">
                  <div className="flex-1 lg:mr-6">
                    <div className="flex items-start space-x-3 mb-3">
                      <div className="flex-1">
                        <NewsStatusBadge article={article} />
                         <h4 onClick={() => openArticleModal(article)} className="text-lg font-semibold leading-tight transition-colors cursor-pointer hover:underline text-gray-900 group-hover:text-blue-700">
                          {article.title}
                        </h4>
                      </div>
                    </div>
                    
                     {article.content && (
                       <p className="text-gray-700 mb-4 leading-relaxed line-clamp-3">
                         {article.content.substring(0, 240)}
                         {article.content.length > 240 ? '…' : ''}
                       </p>
                     )}
                    
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center bg-white px-3 py-1 rounded-full">
                        <CalendarIcon className="mr-2 text-blue-500 w-4 h-4" />
                        {formatDate(article.published_date || article.created_at)}
                      </span>
                      
                      {article.published_time && (
                        <span className="flex items-center bg-white px-3 py-1 rounded-full">
                          <ClockIcon className="mr-2 text-green-500" />
                          {article.published_time}
                        </span>
                      )}
                      
                      {article.views_count && (
                        <span className="flex items-center bg-white px-3 py-1 rounded-full">
                          <ViewIcon className="mr-2 text-purple-500" />
                          {article.views_count} просмотров
                        </span>
                      )}
                      
                      {article.author && (
                        <span className="flex items-center bg-white px-3 py-1 rounded-full">
                          <InfoIcon className="mr-2 text-orange-500" />
                          {article.author}
                        </span>
                      )}
                      
                       {article.url && (
                         <a
                           href={article.url}
                           target="_blank"
                           rel="noopener noreferrer"
                           className="text-blue-600 hover:text-blue-800 underline-offset-2 hover:underline"
                         >
                           Открыть источник
                         </a>
                       )}
                    </div>
                  </div>
                  
                   <div className="flex flex-col sm:flex-row lg:flex-col space-y-2 sm:space-y-0 sm:space-x-2 lg:space-x-0 lg:space-y-2 min-w-0 sm:min-w-[200px] lg:min-w-[180px]">
                     <Button
                       variant="primary"
                       size="sm"
                       icon={PlusIcon}
                       onClick={() => openProjectSelector(article)}
                       className="w-full sm:w-auto lg:w-full touch-target"
                     >
                       В проект
                     </Button>
                     <Button
                       variant="secondary"
                       size="sm"
                       icon={ViewIcon}
                       onClick={() => openArticleModal(article)}
                       className="w-full sm:w-auto lg:w-full touch-target"
                     >
                       Подробнее
                     </Button>
                     <Button
                       variant="ghost"
                       size="sm"
                       icon={ExternalIcon}
                       onClick={() => article.url && window.open(article.url, '_blank')}
                       disabled={!article.url}
                       className="w-full sm:w-auto lg:w-full touch-target"
                     >
                       Источник
                     </Button>
                     {article.has_draft && !article.is_published && (
                       <Button
                         variant="error"
                         size="sm"
                         icon={DeleteIcon}
                         onClick={() => handleDeleteDraft(article)}
                         className="w-full sm:w-auto lg:w-full touch-target"
                       >
                         <span className="hidden sm:inline lg:hidden">Удалить</span>
                         <span className="sm:hidden lg:inline">Удалить черновик</span>
                       </Button>
                     )}
                   </div>
                </div>
              </div>
            ))}
          </div>

          {/* Пагинация */}
          <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
            <div className="text-sm text-gray-600">
              Показано: {news.length} • Страница {currentPage}
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="secondary" size="sm" onClick={goPrev} disabled={!canPrev}>Назад</Button>
              <Button variant="secondary" size="sm" onClick={goNext} disabled={!canNext}>Вперед</Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="w-32 h-32 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-8 border border-gray-200">
            <FilterIcon className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Новости не найдены
          </h3>
          <p className="text-gray-600 mb-3 w-4 h-4">
            В базе данных нет новостей из источника <span className="font-semibold text-blue-600">{selectedSourceData?.label}</span>
          </p>
          <p className="text-gray-500 text-sm mt-6 max-w-lg mx-auto leading-relaxed">
            Попробуйте запустить парсинг новостей на вкладке "Мониторинг новостей" или выберите другой источник для поиска статей
          </p>
          <div className="mt-8 flex justify-center space-x-4">
            <button
              onClick={handleRefresh}
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 font-semibold"
            >
              <RefreshIcon className="mr-2" />
              Обновить данные
            </button>
          </div>
        </div>
      )}

      {/* Simple Article Modal */}
      {isModalOpen && selectedArticle && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-[9990] p-2 sm:p-4">
          <div className="bg-white rounded-xl sm:rounded-2xl w-full max-w-5xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden shadow-2xl border border-gray-100 transform transition-all duration-300">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-4 sm:px-6 md:px-8 py-4 sm:py-6 border-b border-gray-100">
              <div className="flex items-start justify-between">
                <div className="flex-1 pr-2 sm:pr-4 min-w-0">
                  <div className="flex items-center mb-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mr-4 shadow-lg">
                      <NewsIcon className="text-white w-4 h-4" />
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${getSourceColor(selectedArticle.source_site)}`}>
                        {selectedArticle.source_site}
                      </span>
                      <span className="text-gray-400">•</span>
                      <span className="text-sm text-gray-600 font-medium">
                        {formatDate(selectedArticle.published_date || selectedArticle.created_at)}
                      </span>
                    </div>
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 leading-tight">
                    {selectedArticle.title}
                  </h2>
                  {selectedArticle.author && (
                    <p className="text-gray-600 mt-2 flex items-center">
                      <UserIcon className="mr-2 text-gray-400" />
                      {selectedArticle.author}
                    </p>
                  )}
                </div>
                <button
                  onClick={closeArticleModal}
                  className="w-10 h-10 bg-white rounded-xl flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  <XIcon  />
                </button>
              </div>
            </div>
            
            {/* Content */}
            <div className="overflow-y-auto max-h-[calc(90vh-200px)]">
              <div className="p-8">
                {/* Article Stats */}
                <div className="flex items-center space-x-6 mb-6 p-4 bg-gray-50 rounded-xl border border-gray-100">
                  {selectedArticle.published_time && (
                    <div className="flex items-center text-sm text-gray-600">
                      <ClockIcon className="mr-2 text-green-500" />
                      <span className="font-medium">{selectedArticle.published_time}</span>
                    </div>
                  )}
                  {selectedArticle.views_count && (
                    <div className="flex items-center text-sm text-gray-600">
                      <ViewIcon className="mr-2 text-purple-500" />
                      <span className="font-medium">{selectedArticle.views_count} просмотров</span>
                    </div>
                  )}
                  <div className="flex items-center text-sm text-gray-600">
                    <InfoIcon className="mr-2 text-blue-500" />
                    <span className="font-medium">Статья из базы данных</span>
                  </div>
                </div>
                
                {/* Article Content */}
                {selectedArticle.content ? (
                  <div className="prose prose-lg max-w-none">
                    <div className="text-gray-800 leading-relaxed text-lg whitespace-pre-line font-light">
                      {selectedArticle.content}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <WarningIcon className="w-6 h-6 text-gray-400" />
                    </div>
                    <p className="text-gray-500 text-lg font-medium">Содержание статьи недоступно</p>
                    <p className="text-gray-400 text-sm mt-2">Попробуйте перейти к источнику для чтения полной статьи</p>
                  </div>
                )}
              </div>
              
              {/* Footer Actions */}
              <div className="bg-gray-50 px-8 py-6 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <a
                      href={selectedArticle.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 font-semibold"
                    >
                      <ExternalIcon className="mr-2" />
                      Читать на источнике
                    </a>
                    <button
                      onClick={() => openProjectSelector(selectedArticle)}
                      className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105 font-semibold"
                    >
                      <PlusIcon className="mr-2" />
                      Добавить в проект
                    </button>
                  </div>
                  <div className="text-sm text-gray-500">
                    <span className="flex items-center">
                      <GlobalIcon className="mr-2" />
                      {selectedArticle.url ? new URL(selectedArticle.url).hostname : 'Источник недоступен'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Project Selector Modal */}
      <ProjectSelectorModal
        isOpen={isProjectSelectorOpen}
        onClose={closeProjectSelector}
        onSelectProject={handleProjectSelect}
        article={articleToAdd}
      />

      {/* Summary Confirmation Modal */}
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

      {/* Article Editor Modal */}
      {currentStep === 'editing' && generatedArticle && (
        <ArticleEditor
          isOpen={true}
          articleData={generatedArticle}
          onSave={handleArticleSave}
          onPreview={handlePreview}
          onRegenerateImage={handleRegenerateImage}
          onPublish={openBitrixProjectSelector}
          publishLabel={(selectedProject?.code === 'RM') ? 'Скачать' : 'Опубликовать'}
          onClose={resetGenerationState}
          isLoading={isGenerating}
          isPublishing={isGenerating}
        />
      )}

      {/* Article Preview Modal */}
      {currentStep === 'preview' && generatedArticle && selectedProject && (
        <ArticlePreview
          isOpen={true}
          articleData={generatedArticle}
          project={selectedProject}
          onPublish={openBitrixProjectSelector}
          onClose={() => setCurrentStep('editing')}
          isLoading={isGenerating}
        />
      )}

      {/* Публикация отключена */}

      {/* Publish Result Modal */}
      {publishModal.open && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl border border-gray-100">
            <div className="px-6 py-5 border-b bg-gradient-to-r from-green-50 to-emerald-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center">
                  <CheckIcon />
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
                onClick={() => setPublishModal({ open: false, project: null, bitrixId: null, url: null })}
                className="px-5 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Modal */}
      <ProgressModal
        isOpen={showProgressModal}
        onClose={() => !isGenerating && resetGenerationState()}
        currentStep={currentStep}
        isGenerating={isGenerating}
        selectedProject={selectedProject}
        articleTitle={articleToAdd?.title}
      />

      {/* Модальное окно публикации */}
      <PublicationModal
        isOpen={isPublicationModalOpen}
        onClose={() => setIsPublicationModalOpen(false)}
        draftId={publicationData?.draftId}
        projectCode={publicationData?.projectCode}
        onPublish={handlePublicationFromModal}
      />

      {/* Публикация отключена */}

      {/* Уведомление о сохранении черновика при ошибке */}
      {draftErrorNotification && (
        <DraftSavedNotification
          draftId={draftErrorNotification.draftId}
          errorMessage={draftErrorNotification.errorMessage}
          errorStep={draftErrorNotification.errorStep}
          onRetry={draftErrorNotification.onRetry}
          onDismiss={draftErrorNotification.onDismiss}
        />
      )}
    </div>
  )
}

export default FoundNews