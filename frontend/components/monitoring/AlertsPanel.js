import React, { useState } from 'react';
import { FaExclamationCircle } from 'react-icons/fa';
import {
  WarningIcon,
  InfoIcon,
  CheckIcon,
  XIcon,
  ClockIcon,
  ViewIcon,
  FilterIcon
} from '../ui/icons';

import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

const AlertsPanel = ({ data, onAcknowledge }) => {
  const [filter, setFilter] = useState('all'); // all, critical, warning, info
  const [showOnlyActive, setShowOnlyActive] = useState(true);

  if (!data) {
    return (
      <Card>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  const getAlertIcon = (type) => {
    const icons = {
      critical: FaExclamationCircle,
      warning: WarningIcon,
      info: InfoIcon
    };
    return icons[type] || InfoIcon;
  };

  const getAlertColor = (type) => {
    const colors = {
      critical: 'red',
      warning: 'yellow',
      info: 'blue'
    };
    return colors[type] || 'gray';
  };

  const getFilteredAlerts = () => {
    let alerts = data.alerts || [];
    
    if (showOnlyActive) {
      alerts = alerts.filter(alert => !alert.acknowledged);
    }
    
    if (filter !== 'all') {
      alerts = alerts.filter(alert => alert.type === filter);
    }
    
    return alerts;
  };

  const filteredAlerts = getFilteredAlerts();

  const AlertItem = ({ alert }) => {
    const AlertIcon = getAlertIcon(alert.type);
    const color = getAlertColor(alert.type);
    
    return (
      <div className={`relative p-4 rounded-lg border-l-4 border-${color}-500 bg-${color}-50 hover:bg-${color}-100 transition-colors`}>
        {/* Заголовок алерта */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center">
            <AlertIcon className={`text-${color}-600 mr-2 mt-0.5`} />
            <div>
              <h4 className={`font-semibold text-${color}-900`}>
                {alert.title}
              </h4>
              <p className={`text-sm text-${color}-700`}>
                {alert.message}
              </p>
            </div>
          </div>
          
          {/* Бейдж типа */}
          <Badge 
            variant={alert.type === 'critical' ? 'error' : alert.type === 'warning' ? 'warning' : 'info'}
            size="sm"
          >
            {alert.type === 'critical' && 'Критично'}
            {alert.type === 'warning' && 'Предупреждение'}
            {alert.type === 'info' && 'Информация'}
          </Badge>
        </div>

        {/* Детали */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <span className={`text-${color}-600`}>
              <strong>Сервис:</strong> {alert.service}
            </span>
            <span className={`text-${color}-600`}>
              <ClockIcon className="inline mr-1" />
              {new Date(alert.timestamp).toLocaleString('ru-RU')}
            </span>
          </div>
          
          {!alert.acknowledged && onAcknowledge && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onAcknowledge(alert.id)}
              className="ml-2"
            >
              <CheckIcon className="mr-1" />
              Подтвердить
            </Button>
          )}
        </div>

        {/* Индикатор подтверждения */}
        {alert.acknowledged && (
          <div className="absolute top-2 right-2">
            <CheckIcon className="text-green-600" />
          </div>
        )}
      </div>
    );
  };

  return (
    <Card>
      {/* Заголовок панели */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <WarningIcon className="mr-2 text-orange-600" />
            Алерты
          </h3>
          
          {/* Переключатель активных/всех */}
          <div className="flex items-center space-x-2">
            <Button
              size="sm"
              variant={showOnlyActive ? 'primary' : 'secondary'}
              onClick={() => setShowOnlyActive(!showOnlyActive)}
            >
              {showOnlyActive ? 'Активные' : 'Все'}
            </Button>
          </div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="p-2 bg-red-50 rounded">
            <div className="text-sm font-bold text-red-600">
              {data.statistics.critical}
            </div>
            <div className="text-xs text-red-700">Критичных</div>
          </div>
          <div className="p-2 bg-yellow-50 rounded">
            <div className="text-sm font-bold text-yellow-600">
              {data.statistics.warning}
            </div>
            <div className="text-xs text-yellow-700">Предупреждений</div>
          </div>
          <div className="p-2 bg-blue-50 rounded">
            <div className="text-sm font-bold text-blue-600">
              {data.statistics.info}
            </div>
            <div className="text-xs text-blue-700">Информационных</div>
          </div>
          <div className="p-2 bg-green-50 rounded">
            <div className="text-sm font-bold text-green-600">
              {data.statistics.active}
            </div>
            <div className="text-xs text-green-700">Активных</div>
          </div>
        </div>

        {/* Фильтры */}
        <div className="mt-4 flex items-center space-x-2">
          <FilterIcon className="text-gray-500" />
          <div className="flex space-x-1">
            {['all', 'critical', 'warning', 'info'].map(filterType => (
              <Button
                key={filterType}
                size="sm"
                variant={filter === filterType ? 'primary' : 'secondary'}
                onClick={() => setFilter(filterType)}
              >
                {filterType === 'all' && 'Все'}
                {filterType === 'critical' && 'Критичные'}
                {filterType === 'warning' && 'Предупреждения'}
                {filterType === 'info' && 'Информация'}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Список алертов */}
      <div className="p-6">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckIcon className="w-10 h-10 text-green-600 mx-auto mb-3" />
            <h4 className="font-semibold text-gray-900 mb-2">
              {showOnlyActive ? 'Нет активных алертов' : 'Нет алертов'}
            </h4>
            <p className="text-gray-600">
              {showOnlyActive 
                ? 'Все системы работают нормально' 
                : 'История алертов пуста'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {filteredAlerts.map(alert => (
              <AlertItem key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </div>

      {/* Действия */}
      {filteredAlerts.length > 0 && (
        <div className="p-6 border-t border-gray-200">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">
              Показано {filteredAlerts.length} из {data.statistics.total} алертов
            </span>
            
            <div className="flex space-x-2">
              {data.statistics.active > 0 && (
                <>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/admin/monitoring/alerts/clear-all', {
                          method: 'POST'
                        });
                        if (response.ok) {
                          // Обновляем данные после очистки
                          window.location.reload();
                        }
                      } catch (err) {
                        console.error('Error clearing alerts:', err);
                      }
                    }}
                  >
                    Подтвердить все
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="error"
                    onClick={async () => {
                      if (confirm('Это полностью очистит историю алертов. Продолжить?')) {
                        try {
                          const response = await fetch('/api/admin/monitoring/alerts/history', {
                            method: 'DELETE'
                          });
                          if (response.ok) {
                            window.location.reload();
                          }
                        } catch (err) {
                          console.error('Error clearing alerts history:', err);
                        }
                      }
                    }}
                  >
                    Очистить историю
                  </Button>
                </>
              )}
              
              <Button size="sm" variant="primary">
                <ViewIcon className="mr-1" />
                Показать все
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};

export default AlertsPanel;