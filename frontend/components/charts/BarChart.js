import React, { useEffect, useRef } from 'react'

const BarChart = ({ data, title, color = '#3B82F6' }) => {
  const canvasRef = useRef(null)

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

    // Настройки отступов
    const padding = { top: 20, right: 20, bottom: 60, left: 80 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    if (data.length === 0) {
      // Рисуем сообщение "Нет данных"
      ctx.fillStyle = '#6B7280'
      ctx.font = '16px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText('Нет данных', width / 2, height / 2)
      return
    }

    // Находим максимальное значение
    const maxValue = Math.max(...data.map(d => d.value))
    const roundedMax = Math.ceil(maxValue / 1000) * 1000 || 1000

    // Ширина столбца
    const barWidth = chartWidth / data.length * 0.6
    const barSpacing = chartWidth / data.length

    // Рисуем столбцы
    data.forEach((item, index) => {
      const barHeight = (item.value / roundedMax) * chartHeight
      const x = padding.left + index * barSpacing + (barSpacing - barWidth) / 2
      const y = padding.top + chartHeight - barHeight

      // Градиент для столбца
      const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight)
      gradient.addColorStop(0, color)
      gradient.addColorStop(1, color + '80') // Добавляем прозрачность

      // Рисуем столбец
      ctx.fillStyle = gradient
      ctx.fillRect(x, y, barWidth, barHeight)

      // Рисуем границу столбца
      ctx.strokeStyle = color
      ctx.lineWidth = 1
      ctx.strokeRect(x, y, barWidth, barHeight)

      // Рисуем значение над столбцом
      if (barHeight > 20) {
        ctx.fillStyle = '#374151'
        ctx.font = 'bold 12px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'bottom'
        ctx.fillText(
          item.value.toLocaleString() + ' ₽', 
          x + barWidth / 2, 
          y - 5
        )
      }

      // Рисуем подпись оси X
      ctx.fillStyle = '#6B7280'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      
      // Обрезаем длинные подписи
      let label = item.label
      if (label.length > 12) {
        label = label.substring(0, 12) + '...'
      }
      
      ctx.fillText(label, x + barWidth / 2, padding.top + chartHeight + 10)
    })

    // Рисуем оси
    ctx.strokeStyle = '#D1D5DB'
    ctx.lineWidth = 1

    // Ось Y
    ctx.beginPath()
    ctx.moveTo(padding.left, padding.top)
    ctx.lineTo(padding.left, padding.top + chartHeight)
    ctx.stroke()

    // Ось X  
    ctx.beginPath()
    ctx.moveTo(padding.left, padding.top + chartHeight)
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight)
    ctx.stroke()

    // Деления на оси Y
    const stepCount = 5
    const step = roundedMax / stepCount
    
    for (let i = 0; i <= stepCount; i++) {
      const value = i * step
      const y = padding.top + chartHeight - (value / roundedMax) * chartHeight

      // Горизонтальная линия сетки
      if (i > 0) {
        ctx.strokeStyle = '#F3F4F6'
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(padding.left + chartWidth, y)
        ctx.stroke()
      }

      // Подпись значения
      ctx.fillStyle = '#6B7280'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillText(value.toLocaleString(), padding.left - 10, y)
    }

  }, [data, color])

  return (
    <div className="w-full">
      <canvas
        ref={canvasRef}
        style={{ width: '100%', height: '300px' }}
        className="border border-gray-200 rounded"
      />
    </div>
  )
}

export default BarChart