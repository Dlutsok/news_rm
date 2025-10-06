import { useState, useEffect } from 'react'
import { FaSchool, FaBaby, FaHeartbeat } from 'react-icons/fa'
import {
  GlobalIcon
} from './ui/icons'
import apiClient from '@utils/api'

const ProjectSelector = ({ onProjectChange, selectedProject }) => {
  const [projects, setProjects] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const data = await apiClient.request('/api/news-generation/bitrix-projects')
      if (data.success) {
        setProjects(data.projects)
      } else {
        setError('Ошибка загрузки проектов')
      }
      setLoading(false)
    } catch (error) {
      console.error('Error fetching projects:', error)
      setError('Ошибка загрузки проектов')
      setLoading(false)
    }
  }

  const projectIcons = {
    GS: FaSchool,
    PS: FaBaby,
    TS: FaHeartbeat
  }

  const projectColors = {
    GS: 'pink',
    PS: 'blue', 
    TS: 'green'
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="mb-4">
          <div className="h-6 bg-gray-200 rounded w-64"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">{error}</p>
        <button 
          onClick={fetchProjects}
          className="mt-2 px-4 py-2 bg-red-100 text-red-800 rounded hover:bg-red-200"
        >
          Попробовать снова
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">
        Выберите проект, в который хотите добавить эту новость:
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(projects).map(([key, project]) => {
          const Icon = projectIcons[key] || GlobalIcon
          const color = projectColors[key] || 'gray'
          const isSelected = selectedProject === key
          
          return (
            <button
              key={key}
              onClick={() => onProjectChange && onProjectChange(key)}
              className={`p-6 rounded-lg border-2 transition-all duration-200 text-left ${
                isSelected
                  ? `border-${color}-500 bg-${color}-50 shadow-md ring-2 ring-${color}-200`
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center mb-3">
                <Icon className={`w-6 h-6 mr-3 ${
                  isSelected ? `text-${color}-600` : 'text-gray-400'
                }`} />
                <div>
                  <h4 className={`font-semibold ${
                    isSelected ? `text-${color}-900` : 'text-gray-900'
                  }`}>
                    {project.name}
                  </h4>
                  <p className={`text-sm ${
                    isSelected ? `text-${color}-700` : 'text-gray-600'
                  }`}>
                    {project.display_name}
                  </p>
                </div>
              </div>
              
              {/* Индикатор настройки проекта */}
              <div className="flex items-center justify-between">
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                  project.api_url && project.api_token
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    project.api_url && project.api_token
                      ? 'bg-green-400'
                      : 'bg-red-400'
                  }`}></div>
                  {project.api_url && project.api_token ? 'Настроен' : 'Не настроен'}
                </div>
              </div>
            </button>
          )
        })}
      </div>
      
      {selectedProject && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Выбран проект:</strong> {projects[selectedProject]?.display_name}
          </p>
          <p className="text-sm text-blue-600 mt-1">
            Новость будет опубликована в: {projects[selectedProject]?.name}
          </p>
          {(!projects[selectedProject]?.api_url || !projects[selectedProject]?.api_token) && (
            <p className="text-sm text-red-600 mt-2">
              ⚠️ Этот проект не настроен. Обратитесь к администратору для настройки API.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default ProjectSelector