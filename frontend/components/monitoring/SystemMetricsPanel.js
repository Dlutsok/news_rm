import React from 'react';
import {
  ClockIcon,
  InfoIcon,
  MicrochipIcon,
  DatabaseIcon,
  ServerIcon
} from '../ui/icons';

import Card from '../ui/Card';

const SystemMetricsPanel = ({ data }) => {
  if (!data) {
    return (
      <Card>
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <MicrochipIcon className="mr-2 text-blue-600" />
            Системные ресурсы
          </h3>
          <p className="text-sm text-red-600 mt-1">
            ❌ Данные недоступны - проверьте подключение к backend API
          </p>
        </div>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      healthy: 'green',
      warning: 'yellow',
      critical: 'red'
    };
    return colors[status] || 'gray';
  };

  const getProgressBarColor = (percent) => {
    if (percent >= 90) return 'bg-red-500';
    if (percent >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const MetricCard = ({ 
    icon: Icon, 
    title, 
    value, 
    percent, 
    status, 
    details, 
    unit = '%' 
  }) => {
    const statusColor = getStatusColor(status);
    
    return (
      <div className={`bg-gradient-to-br from-white to-gray-50 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow`}>
        {/* Заголовок */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg mr-3 bg-${statusColor}-100`}>
              <Icon className={`w-4 h-4 text-${statusColor}-600`} />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">{title}</h4>
              <p className="text-sm text-gray-600">{details}</p>
            </div>
          </div>
          
          {/* Статус индикатор */}
          <div className={`w-3 h-3 rounded-full bg-${statusColor}-500`}></div>
        </div>

        {/* Основное значение */}
        <div className="mb-3">
          <div className="flex items-baseline justify-between">
            <span className="text-xl font-bold text-gray-900">
              {value}
            </span>
            {percent !== undefined && (
              <span className={`text-sm font-semibold text-${statusColor}-600`}>
                {percent}{unit}
              </span>
            )}
          </div>
        </div>

        {/* Прогресс бар */}
        {percent !== undefined && (
          <div className="mb-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${getProgressBarColor(percent)} transition-all duration-300`}
                style={{ width: `${Math.min(percent, 100)}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Статус текст */}
        <div className="flex items-center justify-between text-sm">
          <span className={`font-medium text-${statusColor}-700`}>
            {status === 'healthy' && 'Нормально'}
            {status === 'warning' && 'Высокая нагрузка'}
            {status === 'critical' && 'Критично'}
          </span>
          
          {status !== 'healthy' && (
            <InfoIcon className={`text-${statusColor}-500`} />
          )}
        </div>
      </div>
    );
  };

  return (
    <Card>
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <MicrochipIcon className="mr-2 text-blue-600" />
          Системные ресурсы
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Мониторинг использования CPU, памяти, диска и сети
        </p>
      </div>
      
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* CPU */}
          <MetricCard
            icon={MicrochipIcon}
            title="Процессор"
            value={`${data.cpu.percent}%`}
            percent={data.cpu.percent}
            status={data.cpu.status}
            details="Загрузка CPU"
          />

          {/* Memory */}
          <MetricCard
            icon={MicrochipIcon}
            title="Оперативная память"
            value={data.memory.used_formatted}
            percent={data.memory.percent}
            status={data.memory.status}
            details={`из ${data.memory.total_formatted}`}
          />

          {/* Disk */}
          <MetricCard
            icon={DatabaseIcon}
            title="Дисковое пространство"
            value={data.disk.used_formatted}
            percent={data.disk.percent}
            status={data.disk.status}
            details={`из ${data.disk.total_formatted}`}
          />
        </div>

        {/* Дополнительная информация */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Сеть */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center mb-3">
              <ServerIcon className="text-blue-600 mr-2" />
              <h4 className="font-semibold text-blue-900">Сетевая активность</h4>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-blue-700">Отправлено:</span>
                <span className="text-sm font-medium text-blue-900">
                  {data.network.sent_formatted}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-blue-700">Получено:</span>
                <span className="text-sm font-medium text-blue-900">
                  {data.network.recv_formatted}
                </span>
              </div>
            </div>
          </div>

          {/* Время работы */}
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center mb-3">
              <ClockIcon className="text-green-600 mr-2" />
              <h4 className="font-semibold text-green-900">Время работы</h4>
            </div>
            <div className="space-y-2">
              <div className="text-xl font-bold text-green-900">
                {data.uptime.formatted}
              </div>
              <div className="text-sm text-green-700">
                Система работает стабильно
              </div>
            </div>
          </div>
        </div>

        {/* Предупреждения */}
        {(data.cpu.status !== 'healthy' || 
          data.memory.status !== 'healthy' || 
          data.disk.status !== 'healthy') && (
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center mb-2">
              <InfoIcon className="text-yellow-600 mr-2" />
              <h4 className="font-semibold text-yellow-900">Рекомендации</h4>
            </div>
            <ul className="text-sm text-yellow-800 space-y-1">
              {data.cpu.status !== 'healthy' && (
                <li>• Высокая загрузка CPU - рассмотрите масштабирование или оптимизацию</li>
              )}
              {data.memory.status !== 'healthy' && (
                <li>• Высокое использование памяти - возможна необходимость в дополнительной RAM</li>
              )}
              {data.disk.status !== 'healthy' && (
                <li>• Мало места на диске - необходимо очистить или расширить хранилище</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </Card>
  );
};

export default SystemMetricsPanel;