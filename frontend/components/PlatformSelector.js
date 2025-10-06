import { useState, useEffect } from 'react'
import { FaSchool, FaBaby, FaHeartbeat } from 'react-icons/fa'
import {

} from './ui/icons'

const PlatformSelector = ({ onPlatformChange, selectedPlatform }) => {
  const [platforms, setPlatforms] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlatforms()
  }, [])

  const fetchPlatforms = async () => {
    try {
      const response = await fetch('/api/admin/platforms')
      const data = await response.json()
      setPlatforms(data.platforms)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching platforms:', error)
      setLoading(false)
    }
  }

  const platformIcons = {
    GS: FaSchool,
    PS: FaBaby,
    TS: FaHeartbeat
  }

  const platformColors = {
    GS: 'pink',
    PS: 'blue', 
    TS: 'green'
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">
        Выберите платформу для парсинга
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(platforms).map(([key, platform]) => {
          const Icon = platformIcons[key] || FaSchool
          const color = platformColors[key] || 'gray'
          const isSelected = selectedPlatform === key
          
          return (
            <button
              key={key}
              onClick={() => onPlatformChange && onPlatformChange(key)}
              className={`p-6 rounded-lg border-2 transition-all duration-200 text-left ${
                isSelected
                  ? `border-${color}-500 bg-${color}-50 shadow-md`
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-center mb-3">
                <Icon className={`w-6 h-6 mr-3 ${
                  isSelected ? `text-${color}-600` : 'text-gray-400'
                }`} />
                <h4 className={`font-semibold ${
                  isSelected ? `text-${color}-900` : 'text-gray-900'
                }`}>
                  {platform.name}
                </h4>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">
                {platform.style}
              </p>
              
              <div className="flex flex-wrap gap-1">
                {platform.topics.slice(0, 3).map((topic, index) => (
                  <span
                    key={index}
                    className={`px-2 py-1 text-xs rounded-full ${
                      isSelected
                        ? `bg-${color}-100 text-${color}-700`
                        : 'bg-gray-100 text-gray-600'
                    }`}
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
            </button>
          )
        })}
      </div>
      
      {selectedPlatform && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Выбрана платформа:</strong> {platforms[selectedPlatform]?.name}
          </p>
          <p className="text-sm text-blue-600 mt-1">
            Новости будут отфильтрованы по темам: {platforms[selectedPlatform]?.topics.join(', ')}
          </p>
        </div>
      )}
    </div>
  )
}

export default PlatformSelector