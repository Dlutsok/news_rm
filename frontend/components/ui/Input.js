import React from 'react';

const Input = ({ 
  label,
  error,
  icon: Icon,
  className = '',
  containerClassName = '',
  ...props 
}) => {
  const baseClasses = 'block w-full border border-gray-300 rounded-lg px-3 py-2 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-corporate-500 focus:border-transparent transition-all duration-200';
  const errorClasses = error ? 'border-error focus:ring-error' : '';
  const iconClasses = Icon ? 'pl-10' : '';

  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Icon className="w-4 h-4 text-gray-400" />
          </div>
        )}
        <input
          className={`${baseClasses} ${errorClasses} ${iconClasses} ${className}`}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1 text-sm text-error">
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;