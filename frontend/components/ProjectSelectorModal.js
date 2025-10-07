import { useState, useEffect } from 'react'
import { FaSchool } from 'react-icons/fa'
import {
  XIcon,
  PlusIcon,
  ResearchIcon,
  HealthIcon,
  MedicalIcon
} from './ui/icons'
import api from '../utils/api'

const ProjectSelectorModal = ({ isOpen, onClose, onSelectProject, article }) => {
  const [platforms, setPlatforms] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isOpen) {
      fetchPlatforms()
    }
  }, [isOpen])

  const fetchPlatforms = async () => {
    try {
      setLoading(true)
      const data = await api.getPlatforms()
      setPlatforms(data.platforms)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching platforms:', error)
      setError('Ошибка загрузки платформ')
      setLoading(false)
    }
  }

  const handleProjectSelect = (platformKey) => {
    const platform = platforms[platformKey]
    if (platform && onSelectProject) {
      // Маппинг кодов платформ на типы проектов для API
      const projectTypeMapping = {
        'GS': 'gynecology.school',
        'TS': 'therapy.school',
        'PS': 'pediatrics.school'
      }
      
      onSelectProject({ 
        code: platformKey, 
        name: platform.name, 
        type: projectTypeMapping[platformKey],
        ...platform 
      }, article)
    }
  }

  const platformIcons = {
    GS: ResearchIcon,
    PS: HealthIcon,
    TS: MedicalIcon,
    RM: ResearchIcon
  }

  const platformColors = {
    GS: 'pink',
    PS: 'blue', 
    TS: 'green',
    RM: 'purple'
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-white rounded-xl sm:rounded-2xl border border-gray-300 p-4 sm:p-6 max-w-4xl w-full max-h-[95vh] sm:max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Выберите платформу для новости
            </h2>
            {article && (
              <p className="text-sm text-gray-600 mt-1">
                {article.title.length > 80 ? `${article.title.substring(0, 80)}...` : article.title}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XIcon  />
          </button>
        </div>
        
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Загрузка платформ...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
            <button 
              onClick={fetchPlatforms}
              className="mt-2 px-4 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200"
            >
              Попробовать снова
            </button>
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(platforms).map(([key, platform]) => {
              const Icon = platformIcons[key] || FaSchool
              const color = platformColors[key] || 'gray'
              
              return (
                <button
                  key={key}
                  onClick={() => handleProjectSelect(key)}
                  className={`p-6 rounded-lg border-2 transition-all duration-200 text-left hover:border-${color}-300 hover:shadow-md group`}
                >
                  <div className="flex items-center mb-3">
                    <Icon className={`w-6 h-6 mr-3 text-${color}-600 group-hover:text-${color}-700`} />
                    <h4 className="font-semibold text-gray-900 group-hover:text-gray-700">
                      {platform.name}
                    </h4>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3">
                    {platform.style}
                  </p>
                  
                  <div className="flex flex-wrap gap-1 mb-3">
                    {platform.topics.slice(0, 3).map((topic, index) => (
                      <span
                        key={index}
                        className={`px-2 py-1 text-xs rounded-full bg-${color}-100 text-${color}-700`}
                      >
                        {topic}
                      </span>
                    ))}
                    {platform.topics.length > 3 && (
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-500">
                        +{platform.topics.length - 3}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-center">
                    <PlusIcon className={`text-${color}-600 group-hover:text-${color}-700`} />
                    <span className={`ml-2 text-sm font-medium text-${color}-600 group-hover:text-${color}-700`}>
                      Добавить в проект
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        )}
        
        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProjectSelectorModal