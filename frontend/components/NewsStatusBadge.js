import React from 'react'
import {
  CheckIcon,
  ClockIcon,
  SaveIcon,
  CalendarIcon
} from './ui/icons'

const NewsStatusBadge = ({ article }) => {
  const getStatusConfig = () => {

    // Приоритет статусов: опубликовано > запланировано > черновик
    if (article.is_published) {
      const projects = article.published_projects && article.published_projects.length > 0
        ? article.published_projects
        : [{ project_code: article.published_project_code, bitrix_id: article.bitrix_id }]

      return {
        type: 'published',
        text: '',
        icon: CheckIcon,
        className: 'bg-green-100 text-green-800 border-green-200',
        details: projects.map(pub => ({
          project: pub.project_code,
          bitrixId: pub.bitrix_id
        }))
      }
    }


    // Проверяем запланированность статьи двумя способами: по флагу is_scheduled или по наличию scheduled_at
    if (article.is_scheduled || (article.scheduled_at && !article.is_published)) {
      return {
        type: 'scheduled',
        text: 'Новость запланирована',
        icon: ClockIcon,
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        details: article.scheduled_at ? new Date(article.scheduled_at).toLocaleString('ru-RU') : null
      }
    }

    // Показываем черновик только если статья НЕ опубликована и НЕ запланирована
    if (article.has_draft && !article.is_published && !article.is_scheduled && !article.scheduled_at) {
      return {
        type: 'draft',
        text: 'У новости есть черновик',
        icon: SaveIcon,
        className: 'bg-orange-100 text-orange-800 border-orange-200',
        details: null
      }
    }

    return null
  }

  const statusConfig = getStatusConfig()

  if (!statusConfig) return null

  const IconComponent = statusConfig.icon

  return (
    <div className="mb-3">
      {statusConfig.type === 'published' && statusConfig.details ? (
        // Множественные компактные плашки для опубликованных
        <div className="flex items-center gap-2 flex-wrap">
          {statusConfig.details.map((detail, idx) => (
            <div key={idx} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-sm font-medium ${statusConfig.className}`}>
              <IconComponent className="w-3.5 h-3.5" />
              <span className="font-semibold">{detail.project}</span>
              {detail.bitrixId && (
                <span className="text-gray-600 text-xs">#{detail.bitrixId}</span>
              )}
            </div>
          ))}
        </div>
      ) : (
        // Обычная плашка для других статусов
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-medium ${statusConfig.className}`}>
          <IconComponent className="text-xs" />
          <span>{statusConfig.text}</span>

          {/* Дополнительная информация для запланированных */}
          {statusConfig.type === 'scheduled' && statusConfig.details && (
            <div className="flex items-center gap-1 ml-2 px-2 py-0.5 bg-white/50 rounded text-xs">
              <CalendarIcon className="text-xs" />
              <span>{statusConfig.details}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default NewsStatusBadge