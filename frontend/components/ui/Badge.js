import React from 'react';

const Badge = ({ 
  variant = 'default', 
  size = 'md', 
  children, 
  className = '' 
}) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    default: 'bg-gray-100 text-gray-800',
    primary: 'bg-corporate-100 text-corporate-700',
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    published: 'bg-green-100 text-green-800 border border-green-200',
    scheduled: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    draft: 'bg-orange-100 text-orange-800 border border-orange-200',
    info: 'bg-blue-100 text-blue-800 border border-blue-200',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-sm',
  };

  return (
    <span className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}>
      {children}
    </span>
  );
};

export default Badge;