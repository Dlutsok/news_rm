import React, { useEffect, useRef } from 'react'

const PieChart = ({ data, title, colors = null }) => {
  const canvasRef = useRef(null)

  const defaultColors = [
    '#8B5CF6', // purple
    '#10B981', // green  
    '#3B82F6', // blue
    '#F59E0B', // amber
    '#EF4444', // red
    '#06B6D4', // cyan
    '#84CC16', // lime
    '#F97316'  // orange
  ]

  useEffect(() => {
    if (!data || data.length === 0) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    
    // Получаем devicePixelRatio для четкости на Retina экранах
    const devicePixelRatio = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    
    // Устанавливаем реальный размер canvas с учетом devicePixelRatio
    canvas.width = rect.width * devicePixelRatio
    canvas.height = rect.height * devicePixelRatio
    
    // Масштабируем контекст
    ctx.scale(devicePixelRatio, devicePixelRatio)
    
    // Устанавливаем размеры для расчетов
    const { width, height } = { width: rect.width, height: rect.height }

    // Очищаем canvas
    ctx.clearRect(0, 0, width, height)

    // Центр круга
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(width, height) / 2 - 20

    // Вычисляем общую сумму
    const total = data.reduce((sum, item) => sum + item.value, 0)
    
    if (total === 0) {
      // Рисуем сообщение "Нет данных"
      ctx.fillStyle = '#6B7280'
      ctx.font = '16px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText('Нет данных', centerX, centerY)
      return
    }

    let currentAngle = -Math.PI / 2 // Начинаем сверху

    // Рисуем сектора
    data.forEach((item, index) => {
      const sliceAngle = (item.value / total) * 2 * Math.PI
      const color = colors ? colors[index] : defaultColors[index % defaultColors.length]

      // Рисуем сектор
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
      ctx.closePath()
      ctx.fillStyle = color
      ctx.fill()
      
      // Рисуем границу
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.stroke()

      // Рисуем подпись если сектор достаточно большой
      if (sliceAngle > 0.1) {
        const labelAngle = currentAngle + sliceAngle / 2
        const labelRadius = radius * 0.7
        const labelX = centerX + Math.cos(labelAngle) * labelRadius
        const labelY = centerY + Math.sin(labelAngle) * labelRadius

        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 12px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        
        const percentage = ((item.value / total) * 100).toFixed(1)
        ctx.fillText(`${percentage}%`, labelX, labelY)
      }

      currentAngle += sliceAngle
    })

  }, [data, colors])

  return (
    <div className="w-full">
      <canvas
        ref={canvasRef}
        style={{ width: '300px', height: '300px' }}
        className="mx-auto border border-gray-200 rounded"
      />
      
      {/* Легенда */}
      <div className="mt-4 space-y-2">
        {data.map((item, index) => {
          const color = colors ? colors[index] : defaultColors[index % defaultColors.length]
          const total = data.reduce((sum, d) => sum + d.value, 0)
          const percentage = total > 0 ? ((item.value / total) * 100).toFixed(1) : 0
          
          return (
            <div key={item.label} className="flex items-center text-sm">
              <div 
                className="w-3 h-3 rounded-full mr-2 flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="flex-1 text-gray-700">{item.label}</span>
              <span className="font-medium text-gray-900 ml-2">
                {item.value.toLocaleString()} ₽ ({percentage}%)
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default PieChart