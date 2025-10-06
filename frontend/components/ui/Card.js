import React from 'react';

const Card = ({ 
  children, 
  title, 
  subtitle,
  className = '',
  headerClassName = '',
  contentClassName = '',
  padding = 'lg',
  shadow = true
}) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6', 
    lg: 'p-8',
  };

  const shadowClass = shadow ? 'shadow-sm border border-gray-100' : 'border border-gray-200';

  return (
    <div className={`bg-white rounded-xl ${shadowClass} ${className}`}>
      {(title || subtitle) && (
        <div className={`border-b border-gray-100 ${paddingClasses[padding]} pb-4 ${headerClassName}`}>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      )}
      <div className={`${title || subtitle ? `${paddingClasses[padding]} pt-6` : paddingClasses[padding]} ${contentClassName}`}>
        {children}
      </div>
    </div>
  );
};

export default Card;