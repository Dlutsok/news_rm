import React from 'react';
import {
  WarningIcon,
  InfoIcon,
  XIcon,
  CheckIcon
} from './icons';

const Alert = ({ 
  variant = 'info', 
  title, 
  children, 
  onClose,
  className = '' 
}) => {
  const variants = {
    success: {
      container: 'bg-green-50 border-green-200 text-green-800',
      icon: CheckIcon,
      iconColor: 'text-green-400',
    },
    error: {
      container: 'bg-red-50 border-red-200 text-red-800',
      icon: WarningIcon,
      iconColor: 'text-red-400',
    },
    warning: {
      container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      icon: WarningIcon,
      iconColor: 'text-yellow-400',
    },
    info: {
      container: 'bg-corporate-50 border-corporate-200 text-corporate-800',
      icon: InfoIcon,
      iconColor: 'text-corporate-400',
    },
  };

  const config = variants[variant];
  const Icon = config.icon;

  return (
    <div className={`border rounded-lg p-4 ${config.container} ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <Icon className={`w-5 h-5 ${config.iconColor}`} />
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className="text-sm font-medium mb-1">
              {title}
            </h3>
          )}
          <div className="text-sm">
            {children}
          </div>
        </div>
        {onClose && (
          <div className="ml-auto pl-3">
            <button
              type="button"
              className={`inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${config.iconColor} hover:bg-opacity-20`}
              onClick={onClose}
            >
              <XIcon className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alert;