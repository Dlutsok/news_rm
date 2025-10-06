import { useState, useEffect } from 'react'
import {
  NewsIcon,
  ClockIcon,
  RobotIcon,
  CheckIcon
} from './ui/icons'

const SystemStats = () => {
  const [parsingStats, setParsingStats] = useState(null)
  const [adaptationStats, setAdaptationStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Добавляем задержку для избежания конфликтов с другими запросами
    const timer = setTimeout(() => {
      fetchStats()
    }, 2000)
    
    return () => clearTimeout(timer)
  }, [])

  const fetchStats = async () => {
    try {
      // Делаем запросы последовательно, а не одновременно
      const parsingResponse = await fetch('/api/admin/stats/parsing')
      const parsingData = await parsingResponse.json()
      setParsingStats(parsingData)
      
      // Небольшая задержка между запросами
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const adaptationResponse = await fetch('/api/admin/stats/adaptation')
      const adaptationData = await adaptationResponse.json()
      setAdaptationStats(adaptationData)
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(j => (
                <div key={j} className="h-20 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const StatCard = ({ icon: Icon, title, value, subtitle, color = 'blue' }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-full bg-${color}-100 mr-4`}>
          <Icon className={`text-${color}-600 w-5 h-5`} />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Parsing Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Статистика парсинга
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={NewsIcon}
            title="Всего спарсено"
            value={parsingStats?.total_parsed || 0}
            subtitle="новостей"
            color="blue"
          />
          
          <StatCard
            icon={ClockIcon}
            title="Сегодня"
            value={parsingStats?.today_parsed || 0}
            subtitle="новостей"
            color="green"
          />
          
          <StatCard
            icon={CheckIcon}
            title="Успешность"
            value={`${(parsingStats?.success_rate || 0).toFixed(1)}%`}
            subtitle="парсинга"
            color="emerald"
          />
          
          <StatCard
            icon={NewsIcon}
            title="Активных источников"
            value={parsingStats?.sources_active || 0}
            subtitle="сайтов"
            color="purple"
          />
        </div>
        
        {parsingStats?.last_parse_time && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Последний парсинг:</strong> {new Date(parsingStats.last_parse_time).toLocaleString('ru-RU')}
            </p>
          </div>
        )}
      </div>

      {/* Adaptation Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Статистика ИИ адаптации
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={RobotIcon}
            title="Всего адаптировано"
            value={adaptationStats?.total_adapted || 0}
            subtitle="новостей"
            color="indigo"
          />
          
          <StatCard
            icon={CheckIcon}
            title="Успешность"
            value={`${(adaptationStats?.success_rate || 0).toFixed(1)}%`}
            subtitle="адаптации"
            color="green"
          />
          
          <StatCard
            icon={ClockIcon}
            title="Среднее время"
            value={`${(adaptationStats?.avg_processing_time || 0).toFixed(1)}с`}
            subtitle="обработки"
            color="yellow"
          />
          
          <StatCard
            icon={NewsIcon}
            title="В очереди"
            value={0}
            subtitle="новостей"
            color="orange"
          />
        </div>
      </div>

      {/* Platform Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Статистика по платформам
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(adaptationStats?.by_platform || {}).map(([platform, count]) => {
            const platformNames = {
              GS: 'Gynecology School',
              PS: 'Pediatrics School', 
              TS: 'Therapy School'
            }
            
            const platformColors = {
              GS: 'pink',
              PS: 'blue',
              TS: 'green'
            }
            
            return (
              <StatCard
                key={platform}
                icon={NewsIcon}
                title={platformNames[platform] || platform}
                value={count}
                subtitle="адаптированных новостей"
                color={platformColors[platform] || 'gray'}
              />
            )
          })}
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">
          Состояние системы
        </h2>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
              <span className="font-medium text-green-900">Парсер новостей</span>
            </div>
            <span className="text-green-600 font-medium">Работает</span>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-3"></div>
              <span className="font-medium text-yellow-900">ИИ адаптация</span>
            </div>
            <span className="text-yellow-600 font-medium">Не настроена</span>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-3"></div>
              <span className="font-medium text-yellow-900">Автопубликация</span>
            </div>
            <span className="text-yellow-600 font-medium">Не настроена</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SystemStats