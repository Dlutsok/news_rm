import React, { useState, useEffect } from 'react';
import {
  WarningIcon,
  CheckIcon,
  XIcon,
  DatabaseIcon,
  ServerIcon,
  RefreshIcon,
  MicrochipIcon,
  HealthIcon,
  ChartIcon
} from '../ui/icons';

import Card from '../ui/Card';
import Button from '../ui/Button';
import Alert from '../ui/Alert';
import Badge from '../ui/Badge';
import ServiceStatusCard from './ServiceStatusCard';
import SystemMetricsPanel from './SystemMetricsPanel';

const SystemMonitoringDashboard = () => {
  const [overview, setOverview] = useState(null);
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [servicesStatus, setServicesStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchAllData();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchAllData, 30000); // Обновление каждые 30 секунд
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Последовательно загружаем данные с лучшим error handling
      let overviewData = null;
      let systemData = null;
      let servicesData = null;

      try {
        const overviewRes = await fetch('/api/proxy/admin/monitoring/overview');
        if (overviewRes.ok) {
          overviewData = await overviewRes.json();
        } else {
          console.warn('Overview endpoint failed:', overviewRes.status);
        }
      } catch (err) {
        console.warn('Overview request failed:', err);
      }

      try {
        const systemRes = await fetch('/api/proxy/admin/monitoring/system');
        if (systemRes.ok) {
          systemData = await systemRes.json();
        } else {
          console.warn('System metrics endpoint failed:', systemRes.status);
        }
      } catch (err) {
        console.warn('System metrics request failed:', err);
      }

      try {
        const servicesRes = await fetch('/api/proxy/admin/monitoring/services');
        if (servicesRes.ok) {
          servicesData = await servicesRes.json();
        } else {
          console.warn('Services status endpoint failed:', servicesRes.status);
        }
      } catch (err) {
        console.warn('Services status request failed:', err);
      }

      // Проверяем что хотя бы один endpoint работает
      if (!overviewData && !systemData && !servicesData) {
        throw new Error('Все endpoints мониторинга недоступны. Проверьте что backend запущен и API работает.');
      }

      setOverview(overviewData);
      setSystemMetrics(systemData);
      setServicesStatus(servicesData);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching monitoring data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };


  const getStatusBadge = (status) => {
    const statusConfig = {
      healthy: { variant: 'success', label: 'Здоров', icon: CheckIcon },
      warning: { variant: 'warning', label: 'Предупреждение', icon: WarningIcon },
      critical: { variant: 'error', label: 'Критично', icon: XIcon }
    };
    
    const config = statusConfig[status] || statusConfig.critical;
    const IconComponent = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center">
        <IconComponent className="mr-1" />
        {config.label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Заголовок загрузки */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Левая часть - заголовок */}
            <div className="flex items-center">
              <div className="bg-gray-600 p-3 rounded-md mr-4 animate-pulse">
                <div className="w-4 h-4 bg-white rounded"></div>
              </div>
              <div>
                <div className="h-6 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-64 animate-pulse"></div>
              </div>
            </div>

            {/* Правая часть - информация и действия */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 lg:gap-6">
              {/* Статус и время обновления */}
              <div className="flex items-center gap-6">
                <div className="text-center sm:text-right">
                  <div className="h-4 bg-gray-200 rounded w-24 mb-1 animate-pulse"></div>
                  <div className="h-5 bg-gray-200 rounded w-16 animate-pulse"></div>
                </div>

                <div className="text-center sm:text-right">
                  <div className="h-4 bg-gray-200 rounded w-32 mb-1 animate-pulse"></div>
                  <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
                </div>
              </div>

              {/* Кнопки действий */}
              <div className="flex items-center space-x-3">
                <div className="h-8 bg-gray-200 rounded w-24 animate-pulse"></div>
                <div className="h-8 bg-gray-200 rounded w-20 animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Skeleton для загрузки */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                    <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-24"></div>
                  </div>
                  <div className="w-12 h-12 bg-gray-200 rounded-md"></div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Skeleton для основного контента */}
        <div className="space-y-6">
          <div className="animate-pulse">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
              <div className="space-y-4">
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              </div>
            </div>
          </div>
          <div className="animate-pulse">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-24 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8">
        {/* Заголовок ошибки */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Левая часть - заголовок */}
            <div className="flex items-center">
              <div className="bg-gray-600 p-3 rounded-md mr-4">
                <ServerIcon className="text-white w-4 h-4" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Мониторинг системы</h1>
                <p className="text-gray-600 mt-1">Отслеживание производительности и состояния компонентов системы</p>
              </div>
            </div>

            {/* Кнопка действия */}
            <div className="flex justify-start lg:justify-end">
              <Button onClick={fetchAllData} variant="primary" icon={RefreshIcon}>
                Попробовать снова
              </Button>
            </div>
          </div>
        </div>

        <Alert variant="error" className="border-red-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <XIcon className="text-red-500 w-4 h-4 mr-3" />
            </div>
            <div>
              <strong className="text-red-900">Ошибка загрузки данных мониторинга:</strong>
              <p className="text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Заголовок */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          {/* Левая часть - заголовок */}
          <div className="flex items-center">
            <div className="bg-gray-600 p-3 rounded-md mr-4">
              <ServerIcon className="text-white w-4 h-4" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Мониторинг системы</h1>
              <p className="text-gray-600 mt-1">Отслеживание производительности и состояния компонентов системы</p>
            </div>
          </div>

          {/* Правая часть - информация и действия */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 lg:gap-6">
            {/* Статус и время обновления */}
            <div className="flex items-center gap-6">
              <div className="text-center sm:text-right">
                <p className="text-sm text-gray-500">Общее состояние</p>
                <div className="mt-1">
                  {getStatusBadge(overview?.overall_status)}
                </div>
              </div>

              <div className="text-center sm:text-right">
                <p className="text-sm text-gray-500">Последнее обновление</p>
                <p className="text-sm font-medium text-gray-900">
                  {lastUpdate ? lastUpdate.toLocaleTimeString('ru-RU') : 'Загрузка...'}
                </p>
              </div>
            </div>

            {/* Кнопки действий */}
            <div className="flex items-center space-x-3">
              <Button
                onClick={() => setAutoRefresh(!autoRefresh)}
                variant={autoRefresh ? 'success' : 'secondary'}
                size="sm"
              >
                {autoRefresh ? 'Авто-обновление' : 'Ручное обновление'}
              </Button>

              <Button onClick={fetchAllData} variant="primary" icon={RefreshIcon}>
                Обновить
              </Button>
            </div>
          </div>
        </div>
      </div>


      {/* Обзорная панель */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Системные ресурсы */}
        <Card padding="lg" className="bg-white border border-gray-200 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Загрузка CPU</p>
              <p className="text-xl font-bold text-gray-900 mt-2">
                {overview?.summary?.system?.cpu_percent || 0}%
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Память: {overview?.summary?.system?.memory_percent || 0}%
              </p>
            </div>
            <div className="bg-gray-600 p-3 rounded-md">
              <MicrochipIcon className="text-white w-4 h-4" />
            </div>
          </div>
        </Card>

        {/* Статус сервисов */}
        <Card padding="lg" className="bg-white border border-gray-200 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Сервисы</p>
              <p className="text-xl font-bold text-gray-900 mt-2">
                {overview?.summary?.services?.healthy || 0}/{overview?.summary?.services?.total || 0}
              </p>
              <p className="text-sm text-gray-500 mt-1">работают исправно</p>
            </div>
            <div className={`p-3 rounded-md ${
              overview?.summary?.services?.critical > 0 ? 'bg-red-600' :
              overview?.summary?.services?.warning > 0 ? 'bg-yellow-600' :
              'bg-green-600'
            }`}>
              <HealthIcon className="text-white w-4 h-4" />
            </div>
          </div>
        </Card>

        {/* База данных */}
        <Card padding="lg" className="bg-white border border-gray-200 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">База данных</p>
              <p className="text-xl font-bold text-gray-900 mt-2">
                {overview?.summary?.database?.active_connections || 0}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                соединений, {overview?.summary?.database?.cache_hit_ratio || 0}% cache
              </p>
            </div>
            <div className="bg-gray-600 p-3 rounded-md">
              <DatabaseIcon className="text-white w-4 h-4" />
            </div>
          </div>
        </Card>

        {/* Время работы */}
        <Card padding="lg" className="bg-white border border-gray-200 hover:shadow-md transition-shadow duration-200">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide">Время работы</p>
              <p className="text-xl font-bold text-gray-900 mt-2">
                {overview?.summary?.system?.uptime_formatted || 'Н/Д'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Диск: {overview?.summary?.system?.disk_percent || 0}%
              </p>
            </div>
            <div className="bg-gray-600 p-3 rounded-md">
              <ChartIcon className="text-white w-4 h-4" />
            </div>
          </div>
        </Card>
      </div>

      {/* Основной контент */}
      <div className="space-y-6">
        {/* Системные метрики */}
        <SystemMetricsPanel data={systemMetrics} />

        {/* Статус сервисов */}
        <Card className="bg-white border border-gray-200">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <ServerIcon className="mr-2 text-gray-600" />
              Статус сервисов
            </h3>
            <p className="text-gray-600 text-sm mt-1">
              Мониторинг состояния всех компонентов системы
            </p>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {servicesStatus?.services && Object.values(servicesStatus.services).map((service) => (
                <ServiceStatusCard key={service.name} service={service} />
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SystemMonitoringDashboard;