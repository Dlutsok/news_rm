import React from 'react';
import {
  CheckIcon,
  WarningIcon,
  XIcon,
  ExternalIcon,
  GlobalIcon,
  ClockIcon,
  ServerIcon,
  ImageIcon
} from '../ui/icons';

import Badge from '../ui/Badge';

const ServiceStatusCard = ({ service }) => {
  const getServiceIcon = (serviceName) => {
    const iconMap = {
      'Backend API': ServerIcon,
      'Image Service': ImageIcon,
      'Frontend': GlobalIcon
    };

    return iconMap[serviceName] || ServerIcon;
  };

  const getStatusConfig = (status) => {
    const configs = {
      healthy: {
        color: 'green',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        icon: CheckIcon,
        text: 'Работает',
        dotColor: 'bg-green-500'
      },
      warning: {
        color: 'yellow',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        icon: WarningIcon,
        text: 'Предупреждение',
        dotColor: 'bg-yellow-500'
      },
      critical: {
        color: 'red',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        icon: XIcon,
        text: 'Недоступен',
        dotColor: 'bg-red-500'
      },
      unknown: {
        color: 'gray',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200',
        icon: ClockIcon,
        text: 'Неизвестно',
        dotColor: 'bg-gray-500'
      }
    };
    
    return configs[status] || configs.unknown;
  };

  const statusConfig = getStatusConfig(service.status);
  const ServiceIcon = getServiceIcon(service.name);
  const StatusIcon = statusConfig.icon;

  const formatResponseTime = (time) => {
    if (time < 1000) {
      return `${Math.round(time)}ms`;
    } else {
      return `${(time / 1000).toFixed(1)}s`;
    }
  };

  const getResponseTimeColor = (time) => {
    if (time > 5000) return 'text-red-600';
    if (time > 1000) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className={`relative border-2 rounded-lg p-4 transition-all duration-200 ${
      statusConfig.bgColor
    } ${statusConfig.borderColor} hover:shadow-md`}>
      {/* Индикатор статуса */}
      <div className={`absolute top-3 right-3 w-3 h-3 rounded-full ${statusConfig.dotColor}`}></div>
      
      {/* Заголовок сервиса */}
      <div className="flex items-center mb-3">
        <div className={`p-2 rounded-lg mr-3 ${
          service.status === 'healthy' ? 'bg-white' : 'bg-white/50'
        }`}>
          <ServiceIcon className={`w-4 h-4 text-${statusConfig.color}-600`} />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">{service.name}</h4>
          <p className="text-sm text-gray-600 truncate">{service.url}</p>
        </div>
      </div>

      {/* Статус и время ответа */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <StatusIcon className={`text-${statusConfig.color}-600 mr-2`} />
          <span className={`text-sm font-medium text-${statusConfig.color}-800`}>
            {statusConfig.text}
          </span>
        </div>
        
        <div className="text-right">
          <div className={`text-sm font-medium ${getResponseTimeColor(service.response_time)}`}>
            {formatResponseTime(service.response_time)}
          </div>
          <div className="text-xs text-gray-500">ответ</div>
        </div>
      </div>

      {/* Сообщение об ошибке */}
      {service.error_message && (
        <div className="mb-3 p-2 bg-white/70 rounded border border-red-200">
          <p className="text-sm text-red-700 font-medium">Ошибка:</p>
          <p className="text-xs text-red-600">{service.error_message}</p>
        </div>
      )}

      {/* Последняя проверка */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Проверено:</span>
        <span>{new Date(service.last_check).toLocaleTimeString('ru-RU')}</span>
      </div>

      {/* Действия */}
      <div className="mt-3 pt-3 border-t border-gray-200 flex justify-between items-center">
        <a
          href={service.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 text-sm flex items-center transition-colors"
        >
          <ExternalIcon className="mr-1" />
          Открыть
        </a>
        
        {/* Дополнительная информация в зависимости от статуса */}
        {service.status === 'healthy' && (
          <Badge variant="success" size="sm">
            Доступен
          </Badge>
        )}
        
        {service.status === 'warning' && (
          <Badge variant="warning" size="sm">
            Медленно
          </Badge>
        )}
        
        {service.status === 'critical' && (
          <Badge variant="error" size="sm">
            Недоступен
          </Badge>
        )}
      </div>
    </div>
  );
};

export default ServiceStatusCard;