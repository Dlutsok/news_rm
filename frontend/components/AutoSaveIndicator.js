import React, { useState, useEffect, useRef } from 'react';
import {
  CheckIcon,
  LoadingIcon,
  WarningIcon
} from './ui/icons';

const AutoSaveIndicator = ({
  data,
  onSave,
  saveInterval = 30000, // Автосохранение каждые 30 секунд
  disabled = false
}) => {
  const [saveStatus, setSaveStatus] = useState('saved'); // saved, saving, error
  const [lastSaved, setLastSaved] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  const dataRef = useRef(data);
  const saveTimeoutRef = useRef(null);
  const lastSavedDataRef = useRef(JSON.stringify(data));

  useEffect(() => {
    // Проверяем, изменились ли данные
    const currentDataStr = JSON.stringify(data);
    const hasChanged = currentDataStr !== lastSavedDataRef.current;

    setHasChanges(hasChanged);
    dataRef.current = data;

    if (hasChanged && !disabled) {
      setSaveStatus('pending');

      // Очищаем предыдущий таймер
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Устанавливаем новый таймер для автосохранения
      saveTimeoutRef.current = setTimeout(() => {
        performSave();
      }, saveInterval);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [data, saveInterval, disabled]);

  const performSave = async () => {
    if (disabled || !hasChanges) return;

    try {
      setSaveStatus('saving');
      await onSave(dataRef.current);

      lastSavedDataRef.current = JSON.stringify(dataRef.current);
      setLastSaved(new Date());
      setSaveStatus('saved');
      setHasChanges(false);
    } catch (error) {
      console.error('Autosave error:', error);
      setSaveStatus('error');
    }
  };

  const formatLastSaved = () => {
    if (!lastSaved) return '';

    const now = new Date();
    const diff = now - lastSaved;
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (minutes > 0) {
      return `${minutes} мин. назад`;
    } else if (seconds > 10) {
      return `${seconds} сек. назад`;
    } else {
      return 'только что';
    }
  };

  const getStatusConfig = () => {
    switch (saveStatus) {
      case 'saving':
        return {
          icon: LoadingIcon,
          className: 'text-blue-500 animate-spin',
          text: 'Сохранение...',
          bgClass: 'bg-blue-50 border-blue-200'
        };
      case 'error':
        return {
          icon: WarningIcon,
          className: 'text-red-500',
          text: 'Ошибка сохранения',
          bgClass: 'bg-red-50 border-red-200'
        };
      case 'pending':
        return {
          icon: LoadingIcon,
          className: 'text-yellow-500',
          text: 'Ожидание сохранения...',
          bgClass: 'bg-yellow-50 border-yellow-200'
        };
      default: // saved
        return {
          icon: CheckIcon,
          className: 'text-green-500',
          text: hasChanges ? 'Есть несохраненные изменения' : 'Все изменения сохранены',
          bgClass: hasChanges ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  if (disabled) {
    return null;
  }

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-md border text-sm ${config.bgClass}`}>
      <Icon className={`h-3 w-3 ${config.className}`} />
      <span className="text-gray-700">{config.text}</span>
      {lastSaved && saveStatus === 'saved' && !hasChanges && (
        <span className="text-gray-500 text-xs">
          · {formatLastSaved()}
        </span>
      )}
    </div>
  );
};

export default AutoSaveIndicator;