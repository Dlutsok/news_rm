import React, { useState, useEffect } from 'react'
import { 
  localToUTC, 
  getMinScheduleTime, 
  getTimeInfo, 
  validateScheduleTime,
  getUserTimezone 
} from '@utils/timezone'

const PublicationModal = ({
  isOpen,
  onClose,
  draftId,
  projectCode,
  onPublish,
  existingDraft = null
}) => {
  const [mode, setMode] = useState('now')
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // Сброс формы при открытии
  useEffect(() => {
    if (isOpen) {
      if (existingDraft && existingDraft.scheduled_at) {
        // Если есть существующий черновик с запланированным временем, заполняем форму
        const scheduledAt = new Date(existingDraft.scheduled_at)
        const userTimezone = getUserTimezone()

        // Конвертируем UTC время в локальное
        const localScheduledDate = new Date(scheduledAt.getTime() - (userTimezone.offset * 60 * 1000))

        setMode('later')
        setScheduledDate(localScheduledDate.toISOString().split('T')[0])
        setScheduledTime(localScheduledDate.toTimeString().slice(0, 5))
      } else {
        // Для новых черновиков устанавливаем режим "сейчас"
        setMode('now')

        // Устанавливаем минимальное время - через час от текущего
        const minTime = getMinScheduleTime()
        setScheduledDate(minTime.date)
        setScheduledTime(minTime.time)
      }

      setError('')
    }
  }, [isOpen, existingDraft])

  const validateDateTime = () => {
    if (mode === 'now') return true
    
    const validation = validateScheduleTime(scheduledDate, scheduledTime)
    if (!validation.isValid) {
      setError(validation.error)
      return false
    }
    
    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateDateTime()) return
    
    setIsLoading(true)
    setError('')
    
    try {
      const publishData = {
        draft_id: draftId,
        project_code: projectCode,
        mode: mode
      }
      
      if (mode === 'later') {
        publishData.scheduled_at = localToUTC(scheduledDate, scheduledTime)
      }
      
      await onPublish(publishData)
      onClose()
      
    } catch (err) {
      setError(err.message || 'Ошибка при публикации')
    } finally {
      setIsLoading(false)
    }
  }

  const getLocalTimeInfo = () => {
    if (mode === 'now' || !scheduledDate || !scheduledTime) return null
    
    return getTimeInfo(scheduledDate, scheduledTime)
  }

  if (!isOpen) return null

  const timeInfo = getLocalTimeInfo()

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" style={{zIndex: 9999}}>
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Публикация новости
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {/* Выбор режима публикации */}
          <div className="space-y-4 mb-6">
            <div className="flex items-center">
              <input
                id="now"
                name="mode"
                type="radio"
                value="now"
                checked={mode === 'now'}
                onChange={(e) => setMode(e.target.value)}
                className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <label htmlFor="now" className="ml-3 block text-sm font-medium text-gray-700">
                Опубликовать сейчас
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="later"
                name="mode"
                type="radio"
                value="later"
                checked={mode === 'later'}
                onChange={(e) => setMode(e.target.value)}
                className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <label htmlFor="later" className="ml-3 block text-sm font-medium text-gray-700">
                Опубликовать позже
              </label>
            </div>
          </div>

          {/* Поля даты и времени */}
          {mode === 'later' && (
            <div className="space-y-4 mb-6">
              <div>
                <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-2">
                  Дата публикации
                </label>
                <input
                  id="date"
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="time" className="block text-sm font-medium text-gray-700 mb-2">
                  Время публикации
                </label>
                <input
                  id="time"
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              {/* Информация о времени */}
              {timeInfo && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-center mb-2">
                    <svg className="w-4 h-4 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-medium text-blue-900">Информация о времени</span>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">Местное время:</span> {timeInfo.local.full}
                    </p>
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Часовой пояс:</span> {timeInfo.local.timezone}
                    </p>
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">UTC:</span> {timeInfo.utc.display}
                    </p>
                    <p className="text-sm text-blue-600 font-medium">
                      {timeInfo.relative}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Ошибка */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Кнопки */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Отменить
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 w-4 h-4 text-white inline" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Сохранение...
                </>
              ) : (
                mode === 'now' ? 'Опубликовать' : 'Запланировать'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default PublicationModal