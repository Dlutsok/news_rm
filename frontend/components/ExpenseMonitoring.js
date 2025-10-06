import React, { useState, useEffect, useMemo } from 'react'
import {
  UsersIcon,
  FilterIcon,
  NewsIcon,
  ViewIcon,
  ViewIconSlash,
  HealthIcon,
  MedicalIcon,
  ImageIcon,
  CommentsIcon,
  RubleIcon,
  ProjectIcon,
  PieChartIcon,
  DownloadIcon
} from './ui/icons'
import Card from './ui/Card'
import Button from './ui/Button'
import Input from './ui/Input'
import Badge from './ui/Badge'
import apiClient from '@utils/api'

const ExpenseMonitoring = () => {
  // Состояние данных
  const [expenses, setExpenses] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Состояние фильтров
  const [filters, setFilters] = useState({
    dateFrom: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 дней назад
    dateTo: new Date().toISOString().split('T')[0], // сегодня
    userId: '',
    project: '',
    expenseType: ''
  })

  // Состояние UI
  const [showFilters, setShowFilters] = useState(true)
  const [showCharts, setShowCharts] = useState(true)

  // Конфигурация проектов (используем правильные ID из backend)
  const projects = [
    { id: 'gynecology.school', name: 'Gynecology School', icon: HealthIcon, color: 'pink' },
    { id: 'therapy.school', name: 'Therapy School', icon: MedicalIcon, color: 'green' },
    { id: 'pediatrics.school', name: 'Pediatrics School', icon: HealthIcon, color: 'blue' },
  ]

  // Типы расходов
  const expenseTypes = [
    { id: 'news_creation', name: 'Создание новости', cost: 40, icon: NewsIcon, color: 'blue' },
    { id: 'photo_regeneration', name: 'Перегенерация фото', cost: 10, icon: ImageIcon, color: 'green' },
    { id: 'gpt_message', name: 'GPT сообщение', cost: 5, icon: CommentsIcon, color: 'purple' },
    { id: 'telegram_post', name: 'Создание Telegram поста', cost: 20, icon: CommentsIcon, color: 'orange' }
  ]

  // Загрузка данных
  useEffect(() => {
    loadData()
  }, [filters])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Формируем query string для фильтров
      const queryParams = new URLSearchParams()
      if (filters.dateFrom) queryParams.append('date_from', filters.dateFrom)
      if (filters.dateTo) queryParams.append('date_to', filters.dateTo)
      if (filters.userId) queryParams.append('user_id', filters.userId)
      if (filters.project) queryParams.append('project', filters.project)
      if (filters.expenseType) queryParams.append('expense_type', filters.expenseType)

      const queryString = queryParams.toString()
      const expensesUrl = `/api/expenses${queryString ? `?${queryString}` : ''}`

      // Параллельная загрузка данных
      const [expensesResponse, usersResponse] = await Promise.all([
        apiClient.request(expensesUrl, {
          method: 'GET'
        }),
        apiClient.request('/api/users')
      ])

      const expensesData = expensesResponse.expenses || []
      setExpenses(expensesData)
      setUsers(usersResponse.users || [])
    } catch (err) {
      console.error('Error loading expense data:', err)
      setError(err.message)
      setExpenses([])
      setUsers([])
    } finally {
      setLoading(false)
    }
  }


  // Фильтрация данных
  const filteredExpenses = useMemo(() => {
    return expenses.filter(expense => {
      if (filters.userId && expense.userId !== parseInt(filters.userId)) return false
      if (filters.project && expense.project !== filters.project) return false
      if (filters.expenseType && expense.expenseType !== filters.expenseType) return false
      if (filters.dateFrom && expense.date < filters.dateFrom) return false
      if (filters.dateTo && expense.date > filters.dateTo) return false
      return true
    })
  }, [expenses, filters])

  // Сводная статистика
  const statistics = useMemo(() => {
    const total = filteredExpenses.reduce((sum, expense) => sum + expense.amount, 0)
    
    const byProject = projects.map(project => {
      // Фильтруем расходы по проекту (используем поле project из API)
      const projectExpenses = filteredExpenses.filter(e => e.project === project.id)
      const amount = projectExpenses.reduce((sum, e) => sum + e.amount, 0)
      const count = projectExpenses.length
      
      
      return {
        ...project,
        amount,
        count
      }
    })

    // Создаем статистику по пользователям на основе расходов (не требует API пользователей)
    const userExpenseMap = {}
    filteredExpenses.forEach(expense => {
      if (!userExpenseMap[expense.userId]) {
        userExpenseMap[expense.userId] = {
          id: expense.userId,
          username: expense.user,
          amount: 0,
          count: 0
        }
      }
      userExpenseMap[expense.userId].amount += expense.amount
      userExpenseMap[expense.userId].count += 1
    })
    
    const byUser = Object.values(userExpenseMap).filter(user => user.amount > 0)

    const byType = expenseTypes.map(type => ({
      ...type,
      amount: filteredExpenses
        .filter(e => e.expenseType === type.id)
        .reduce((sum, e) => sum + e.amount, 0),
      count: filteredExpenses.filter(e => e.expenseType === type.id).length
    }))

    return { total, byProject, byUser, byType }
  }, [filteredExpenses, users])

  // Обработчики фильтров
  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  const resetFilters = () => {
    setFilters({
      dateFrom: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      dateTo: new Date().toISOString().split('T')[0],
      userId: '',
      project: '',
      expenseType: ''
    })
  }

  // Экспорт данных в CSV
  const exportToCSV = () => {
    const headers = ['Дата', 'Пользователь', 'Проект', 'Тип расхода', 'Сумма', 'Описание']
    const rows = filteredExpenses.map(expense => [
      expense.date,
      expense.user,
      expense.projectName,
      expense.expenseTypeName,
      expense.amount,
      expense.description
    ])

    const csvContent = [headers, ...rows]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `expenses_${filters.dateFrom}_${filters.dateTo}.csv`
    link.click()
  }

  // Экспорт данных в XLSX (упрощенная версия)
  const exportToXLSX = () => {
    // Создаем HTML таблицу для экспорта в Excel
    const headers = ['Дата', 'Пользователь', 'Проект', 'Тип расхода', 'Сумма', 'Описание']
    
    let htmlContent = `
      <table border="1">
        <thead>
          <tr>
            ${headers.map(header => `<th>${header}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
    `
    
    filteredExpenses.forEach(expense => {
      htmlContent += `
        <tr>
          <td>${expense.date}</td>
          <td>${expense.user}</td>
          <td>${expense.projectName}</td>
          <td>${expense.expenseTypeName}</td>
          <td>${expense.amount}</td>
          <td>${expense.description}</td>
        </tr>
      `
    })
    
    htmlContent += `
        </tbody>
      </table>
    `

    const blob = new Blob([htmlContent], { 
      type: 'application/vnd.ms-excel;charset=utf-8;' 
    })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `expenses_${filters.dateFrom}_${filters.dateTo}.xlsx`
    link.click()
  }

  // Экспорт сводки в CSV
  const exportSummaryToCSV = () => {
    let csvContent = 'Сводка расходов\n\n'
    csvContent += `Общая сумма,${statistics.total}\n`
    csvContent += `Количество операций,${filteredExpenses.length}\n\n`
    
    csvContent += 'Расходы по проектам\n'
    csvContent += 'Проект,Сумма,Количество операций\n'
    statistics.byProject.forEach(project => {
      if (project.amount > 0) {
        csvContent += `"${project.name}",${project.amount},${project.count}\n`
      }
    })
    
    csvContent += '\nРасходы по пользователям\n'
    csvContent += 'Пользователь,Сумма,Количество операций\n'
    statistics.byUser.forEach(user => {
      csvContent += `"${user.username}",${user.amount},${user.count}\n`
    })

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `expenses_summary_${filters.dateFrom}_${filters.dateTo}.csv`
    link.click()
  }

  // Получение иконки проекта
  const getProjectIcon = (projectId) => {
    const project = projects.find(p => p.id === projectId)
    return project ? project.icon : ProjectIcon
  }

  // Получение цвета проекта
  const getProjectColor = (projectId) => {
    const project = projects.find(p => p.id === projectId)
    return project ? project.color : 'gray'
  }

  // Получение иконки типа расхода
  const getExpenseTypeIcon = (typeId) => {
    const type = expenseTypes.find(t => t.id === typeId)
    return type ? type.icon : RubleIcon
  }

  if (error && expenses.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center py-8">
          <div className="text-red-600 w-4 h-4 mb-2">Ошибка загрузки данных</div>
          <div className="text-gray-600 mb-4">{error}</div>
          <Button onClick={loadData} variant="primary">
            Попробовать снова
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <RubleIcon className="mr-3 text-green-600" />
            Мониторинг расходов
          </h1>
          <p className="text-gray-600 mt-1">
            Аналитика затрат на создание контента и использование ИИ
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
          <div className="flex items-center space-x-2">
            <Button
              onClick={() => setShowFilters(!showFilters)}
              variant={showFilters ? "primary" : "secondary"}
              icon={FilterIcon}
              size="sm"
              className="flex-1 sm:flex-initial"
            >
              <span className="hidden sm:inline">{showFilters ? <ViewIconSlash className="mr-2" /> : <ViewIcon className="mr-2" />}</span>
              Фильтры
            </Button>
            <Button
              onClick={() => setShowCharts(!showCharts)}
              variant={showCharts ? "primary" : "secondary"}
              icon={PieChartIcon}
              size="sm"
              className="flex-1 sm:flex-initial"
            >
              <span className="hidden sm:inline">{showCharts ? <ViewIconSlash className="mr-2" /> : <ViewIcon className="mr-2" />}</span>
              Графики
            </Button>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              onClick={exportToCSV}
              variant="success"
              icon={DownloadIcon}
              size="sm"
              className="flex-1 sm:flex-initial"
            >
              CSV
            </Button>
            <Button
              onClick={exportToXLSX}
              variant="success"
              icon={DownloadIcon}
              size="sm"
              className="flex-1 sm:flex-initial"
            >
              XLSX
            </Button>
            <Button
              onClick={exportSummaryToCSV}
              variant="secondary"
              icon={DownloadIcon}
              size="sm"
              className="flex-1 sm:flex-initial"
            >
              <span className="hidden sm:inline">Сводка</span>
              <span className="sm:hidden">Итог</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Фильтры */}
      {showFilters && (
        <Card padding="lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <FilterIcon className="mr-2 text-blue-600" />
              Фильтры
            </h3>
            <Button onClick={resetFilters} variant="secondary" size="sm">
              Сбросить
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Дата от */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Дата от
              </label>
              <Input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              />
            </div>

            {/* Дата до */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Дата до
              </label>
              <Input
                type="date"
                value={filters.dateTo}
                onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              />
            </div>

            {/* Пользователь */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Пользователь
              </label>
              <select
                value={filters.userId}
                onChange={(e) => handleFilterChange('userId', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все пользователи</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.username}
                  </option>
                ))}
              </select>
            </div>

            {/* Проект */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Проект
              </label>
              <select
                value={filters.project}
                onChange={(e) => handleFilterChange('project', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все проекты</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Тип расхода */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Тип расхода
              </label>
              <select
                value={filters.expenseType}
                onChange={(e) => handleFilterChange('expenseType', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Все типы</option>
                {expenseTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.name} ({type.cost} ₽)
                  </option>
                ))}
              </select>
            </div>
          </div>
        </Card>
      )}

      {/* Сводная статистика */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Общая статистика */}
        <Card padding="lg" className="lg:col-span-1">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
              <RubleIcon className="w-6 h-6 text-green-600" />
            </div>
            <div className="text-2xl font-bold text-gray-900">{statistics.total.toLocaleString()} ₽</div>
            <div className="text-sm text-gray-600">Общие расходы</div>
            <div className="text-xs text-gray-500 mt-1">
              {filteredExpenses.length} операций
            </div>
          </div>
        </Card>

        {/* Статистика по проектам */}
        <Card padding="lg" className="lg:col-span-3">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <ProjectIcon className="mr-2 text-blue-600" />
            По проектам
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {statistics.byProject.map(project => {
              const Icon = project.icon
              return (
                <div key={project.id} className="text-center p-4 border border-gray-200 rounded-lg">
                  <div className={`w-10 h-10 mx-auto bg-${project.color}-100 rounded-full flex items-center justify-center mb-2`}>
                    <Icon className={`text-${project.color}-600`} />
                  </div>
                  <div className="text-lg font-semibold text-gray-900">
                    {project.amount.toLocaleString()} ₽
                  </div>
                  <div className="text-sm text-gray-600">{project.name}</div>
                  <div className="text-xs text-gray-500">{project.count} операций</div>
                </div>
              )
            })}
          </div>
        </Card>
      </div>


      {/* Дополнительная статистика по типам расходов */}
      {showCharts && (
        <Card padding="lg">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <RubleIcon className="mr-2 text-green-600" />
            Расходы по типам операций
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {statistics.byType.map(type => {
              const IconComponent = getExpenseTypeIcon(type.id)
              const percentage = statistics.total > 0 ? (type.amount / statistics.total * 100).toFixed(1) : 0
              
              return (
                <div key={type.id} className="text-center p-6 border border-gray-200 rounded-lg">
                  <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <IconComponent className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="text-lg font-semibold text-gray-900 mb-1">
                    {type.amount.toLocaleString()} ₽
                  </div>
                  <div className="text-sm text-gray-600 mb-2">{type.name}</div>
                  <div className="text-xs text-gray-500">
                    {type.count} операций ({percentage}%)
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {type.cost} ₽ за операцию
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Таблица расходов */}
      <Card padding="lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Детальный отчет ({filteredExpenses.length} записей)
          </h3>
          {filteredExpenses.length > 0 && (
            <Badge variant="info">
              Итого: {statistics.total.toLocaleString()} ₽
            </Badge>
          )}
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <div className="text-gray-600">Загрузка данных...</div>
          </div>
        ) : filteredExpenses.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-600 mb-2">Нет данных для отображения</div>
            <div className="text-sm text-gray-500">Попробуйте изменить фильтры</div>
          </div>
        ) : (
          <div>
            {/* Мобильная версия (карточки) */}
            <div className="block lg:hidden">
              <div className="space-y-4">
                {filteredExpenses.map((expense) => {
                  const ProjectIconComponent = getProjectIcon(expense.project)
                  const ExpenseIconComponent = getExpenseTypeIcon(expense.expenseType)
                  
                  return (
                    <div key={expense.id} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <ProjectIconComponent className={`mr-2 text-${getProjectColor(expense.project)}-600`} />
                          <span className="font-medium text-gray-900">{expense.projectName}</span>
                        </div>
                        <span className="text-lg font-semibold text-gray-900">
                          {expense.amount.toLocaleString()} ₽
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-500">Дата:</span>
                          <div className="font-medium text-gray-900">
                            {new Date(expense.date).toLocaleDateString('ru-RU')}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-500">Пользователь:</span>
                          <div className="font-medium text-gray-900">{expense.user}</div>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-500">Тип расхода:</span>
                          <div className="flex items-center mt-1">
                            <ExpenseIconComponent className="mr-2 text-blue-600" />
                            <span className="font-medium text-gray-900">{expense.expenseTypeName}</span>
                          </div>
                        </div>
                        {expense.description && (
                          <div className="col-span-2">
                            <span className="text-gray-500">Описание:</span>
                            <div className="text-gray-900 mt-1">{expense.description}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Десктопная версия (таблица) */}
            <div className="hidden lg:block overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Дата
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Пользователь
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Проект
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Тип расхода
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Сумма
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Описание
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredExpenses.map((expense, index) => {
                    const ProjectIconComponent = getProjectIcon(expense.project)
                    const ExpenseIconComponent = getExpenseTypeIcon(expense.expenseType)
                    
                    return (
                      <tr key={expense.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(expense.date).toLocaleDateString('ru-RU')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                              <UsersIcon className="text-gray-600 text-sm" />
                            </div>
                            <div className="text-sm font-medium text-gray-900">
                              {expense.user}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <ProjectIconComponent className={`mr-2 text-${getProjectColor(expense.project)}-600`} />
                            <span className="text-sm text-gray-900">{expense.projectName}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <ExpenseIconComponent className="mr-2 text-blue-600" />
                            <span className="text-sm text-gray-900">{expense.expenseTypeName}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-semibold text-gray-900">
                            {expense.amount.toLocaleString()} ₽
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {expense.description}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}

export default ExpenseMonitoring