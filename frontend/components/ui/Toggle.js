import React from 'react';

const Toggle = ({
  checked = false,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}) => {
  return (
    <div className={`flex items-start ${className}`}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => !disabled && onChange && onChange(!checked)}
        disabled={disabled}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-corporate-500 focus:ring-offset-2 ${
          checked ? 'bg-corporate-500' : 'bg-gray-200'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <span
          aria-hidden="true"
          className={`pointer-events-none inline-block w-5 h-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>

      {(label || description) && (
        <div className="ml-3">
          {label && (
            <p className="text-sm font-medium text-gray-900">{label}</p>
          )}
          {description && (
            <p className="text-xs text-gray-500">{description}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Toggle;


