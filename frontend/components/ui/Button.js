import React from 'react';
import { LuLoader2 } from 'react-icons/lu';

const Button = ({ 
  variant = 'primary', 
  size = 'md', 
  loading = false, 
  disabled = false,
  icon: Icon,
  children, 
  className = '',
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-corporate-500 text-white hover:bg-corporate-600 focus:ring-corporate-500 disabled:bg-gray-300',
    secondary: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-corporate-500 disabled:bg-gray-100',
    success: 'bg-success text-white hover:bg-green-600 focus:ring-success disabled:bg-gray-300',
    error: 'bg-error text-white hover:bg-red-600 focus:ring-error disabled:bg-gray-300',
    ghost: 'text-corporate-500 hover:bg-corporate-50 focus:ring-corporate-500 disabled:text-gray-400',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm rounded-lg',
    md: 'px-4 py-2 text-sm rounded-lg',
    lg: 'px-6 py-3 text-base rounded-xl',
  };

  const isDisabled = disabled || loading;

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <>
          <LuLoader2 className="animate-spin mr-2 w-4 h-4" />
          {children}
        </>
      ) : (
        <>
          {Icon && <Icon className="mr-2 w-4 h-4" />}
          {children}
        </>
      )}
    </button>
  );
};

export default Button;