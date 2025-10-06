import { format, parseISO, addHours } from 'date-fns'
import { ru } from 'date-fns/locale'

/**
 * Утилиты для работы с временными зонами
 */

/**
 * Получить текущую временную зону пользователя
 */
export const getUserTimezone = () => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

/**
 * Получить смещение временной зоны в минутах
 */
export const getTimezoneOffset = () => {
  return new Date().getTimezoneOffset()
}

/**
 * Преобразовать локальное время в UTC
 * @param {string} dateStr - Дата в формате YYYY-MM-DD
 * @param {string} timeStr - Время в формате HH:MM
 * @returns {string} ISO строка в UTC
 */
export const localToUTC = (dateStr, timeStr) => {
  // НЕ КОНВЕРТИРУЕМ! Возвращаем московское время как есть
  // Backend теперь работает с московским временем напрямую
  return `${dateStr}T${timeStr}:00+03:00`
}

/**
 * Преобразовать UTC в локальное время
 * @param {string} utcString - ISO строка в UTC
 * @returns {Object} Объект с локальными датой и временем
 */
export const utcToLocal = (utcString) => {
  const date = parseISO(utcString)
  return {
    date: format(date, 'yyyy-MM-dd'),
    time: format(date, 'HH:mm'),
    display: format(date, 'dd.MM.yyyy HH:mm', { locale: ru }),
    fullDisplay: format(date, 'dd MMMM yyyy, HH:mm', { locale: ru })
  }
}

/**
 * Форматировать дату с учетом временной зоны
 * @param {string} isoString - ISO строка
 * @param {string} formatStr - Формат даты (по умолчанию 'dd.MM.yyyy HH:mm')
 * @returns {string} Отформатированная строка
 */
export const formatWithTimezone = (isoString, formatStr = 'dd.MM.yyyy HH:mm') => {
  if (!isoString) return '-'
  
  try {
    const date = parseISO(isoString)
    return format(date, formatStr, { locale: ru })
  } catch (error) {
    console.error('Error formatting date:', error)
    return isoString
  }
}

/**
 * Получить минимальное время для планирования (текущее время + 1 час)
 * @returns {Object} Объект с минимальными датой и временем
 */
export const getMinScheduleTime = () => {
  const now = addHours(new Date(), 1)
  return {
    date: format(now, 'yyyy-MM-dd'),
    time: format(now, 'HH:mm'),
    iso: now.toISOString()
  }
}

/**
 * Проверить, что время в будущем
 * @param {string} dateStr - Дата в формате YYYY-MM-DD
 * @param {string} timeStr - Время в формате HH:MM
 * @returns {boolean} true если время в будущем
 */
export const isFutureTime = (dateStr, timeStr) => {
  const year = parseInt(dateStr.split('-')[0])
  const month = parseInt(dateStr.split('-')[1]) - 1
  const day = parseInt(dateStr.split('-')[2])
  const hour = parseInt(timeStr.split(':')[0])
  const minute = parseInt(timeStr.split(':')[1])
  
  const scheduledTime = new Date(year, month, day, hour, minute)
  return scheduledTime > new Date()
}

/**
 * Получить информацию о времени для отображения пользователю
 * @param {string} dateStr - Дата в формате YYYY-MM-DD
 * @param {string} timeStr - Время в формате HH:MM
 * @returns {Object} Объект с информацией о времени
 */
export const getTimeInfo = (dateStr, timeStr) => {
  if (!dateStr || !timeStr) return null

  const year = parseInt(dateStr.split('-')[0])
  const month = parseInt(dateStr.split('-')[1]) - 1
  const day = parseInt(dateStr.split('-')[2])
  const hour = parseInt(timeStr.split(':')[0])
  const minute = parseInt(timeStr.split(':')[1])
  
  const localDateTime = new Date(year, month, day, hour, minute)
  const utcDateTime = new Date(localDateTime.toISOString())
  
  return {
    local: {
      display: format(localDateTime, 'dd.MM.yyyy HH:mm', { locale: ru }),
      full: format(localDateTime, 'dd MMMM yyyy, HH:mm', { locale: ru }),
      timezone: getUserTimezone()
    },
    utc: {
      display: format(utcDateTime, 'dd.MM.yyyy HH:mm', { locale: ru }) + ' UTC',
      iso: localDateTime.toISOString()
    },
    relative: getRelativeTime(localDateTime)
  }
}

/**
 * Получить относительное время ("через 2 часа", "завтра в 15:00" и т.д.)
 * @param {Date} date - Дата
 * @returns {string} Относительное время
 */
export const getRelativeTime = (date) => {
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  
  if (diffMs < 0) return 'в прошлом'
  
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 60) {
    return `через ${diffMinutes} мин.`
  } else if (diffHours < 24) {
    return `через ${diffHours} ч.`
  } else if (diffDays === 1) {
    return `завтра в ${format(date, 'HH:mm')}`
  } else if (diffDays < 7) {
    return `через ${diffDays} дн. в ${format(date, 'HH:mm')}`
  } else {
    return format(date, 'dd.MM.yyyy HH:mm', { locale: ru })
  }
}

/**
 * Создать компонент отображения времени с подсказкой
 * @param {string} isoString - ISO строка времени
 * @param {Object} options - Опции отображения
 * @returns {Object} React компонент
 */
export const TimeDisplay = ({ isoString, showRelative = false, showUTC = false }) => {
  if (!isoString) return <span>-</span>

  const timeInfo = utcToLocal(isoString)
  const relativeTime = showRelative ? getRelativeTime(parseISO(isoString)) : null
  
  return (
    <div className="group relative">
      <span className="cursor-help">
        {timeInfo.display}
        {showRelative && relativeTime && (
          <span className="text-xs text-gray-500 ml-1">({relativeTime})</span>
        )}
      </span>
      
      {/* Подсказка */}
      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-10">
        <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
          <div>Местное: {timeInfo.fullDisplay}</div>
          <div>Часовой пояс: {getUserTimezone()}</div>
          {showUTC && <div>UTC: {format(parseISO(isoString), 'dd.MM.yyyy HH:mm')} UTC</div>}
          <div className="absolute top-full left-2 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </div>
  )
}

/**
 * Валидация времени для планирования
 * @param {string} dateStr - Дата
 * @param {string} timeStr - Время
 * @returns {Object} Результат валидации
 */
export const validateScheduleTime = (dateStr, timeStr) => {
  if (!dateStr || !timeStr) {
    return {
      isValid: false,
      error: 'Укажите дату и время публикации'
    }
  }
  
  if (!isFutureTime(dateStr, timeStr)) {
    return {
      isValid: false,
      error: 'Время публикации должно быть в будущем'
    }
  }
  
  // Проверяем, что время не слишком далеко в будущем (например, больше года)
  const year = parseInt(dateStr.split('-')[0])
  const month = parseInt(dateStr.split('-')[1]) - 1
  const day = parseInt(dateStr.split('-')[2])
  const hour = parseInt(timeStr.split(':')[0])
  const minute = parseInt(timeStr.split(':')[1])
  
  const scheduledTime = new Date(year, month, day, hour, minute)
  const oneYearFromNow = addHours(new Date(), 8760) // 365 * 24
  
  if (scheduledTime > oneYearFromNow) {
    return {
      isValid: false,
      error: 'Нельзя планировать публикацию более чем на год вперед'
    }
  }
  
  return { isValid: true }
}