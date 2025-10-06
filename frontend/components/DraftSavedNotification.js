import React, { useState, useEffect } from 'react';
import {
  SaveIcon,
  XIcon,
  RefreshIcon,
  DocumentIcon
} from './ui/icons';
import Alert from '@components/ui/Alert';
import Button from '@components/ui/Button';

const DraftSavedNotification = ({
  draftId,
  errorMessage,
  errorStep,
  onRetry,
  onDismiss,
  autoHide = true,
  hideDelay = 10000 // 10 секунд
}) => {
  const [visible, setVisible] = useState(true);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (autoHide && hideDelay > 0) {
      const timer = setTimeout(() => {
        setVisible(false);
        if (onDismiss) onDismiss();
      }, hideDelay);

      return () => clearTimeout(timer);
    }
  }, [autoHide, hideDelay, onDismiss]);

  const handleRetry = async () => {
    if (onRetry) {
      try {
        setRetrying(true);
        await onRetry(draftId);
        setVisible(false);
        if (onDismiss) onDismiss();
      } catch (error) {
        console.error('Retry failed:', error);
        setRetrying(false);
      }
    }
  };

  const handleDismiss = () => {
    setVisible(false);
    if (onDismiss) onDismiss();
  };

  const getStepDisplayName = (step) => {
    const stepNames = {
      'summary': 'создании выжимки',
      'generation': 'генерации статьи',
      'publication': 'публикации',
      'image_generation': 'генерации изображения'
    };
    return stepNames[step] || step;
  };

  if (!visible) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-md">
      <Alert
        variant="warning"
        onClose={handleDismiss}
        className="shadow-lg"
      >
        <div className="flex items-start space-x-3">
          <SaveIcon className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-amber-800 mb-1">
              Черновик сохранен для восстановления
            </h4>
            <div className="text-sm text-amber-700 space-y-1">
              <p>
                Произошла ошибка при {getStepDisplayName(errorStep)}, но ваш прогресс сохранен
                в черновике #{draftId}.
              </p>
              {errorMessage && (
                <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded border">
                  <strong>Ошибка:</strong> {errorMessage}
                </p>
              )}
            </div>

            <div className="mt-3 flex items-center space-x-2">
              <Button
                size="sm"
                variant="primary"
                onClick={handleRetry}
                disabled={retrying}
                className="flex items-center space-x-1 bg-amber-600 hover:bg-amber-700"
              >
                <RefreshIcon className={`h-3 w-3 ${retrying ? 'animate-spin' : ''}`} />
                <span>{retrying ? 'Восстановление...' : 'Попробовать снова'}</span>
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={handleDismiss}
                className="text-amber-700 hover:text-amber-900"
              >
                Позже
              </Button>
            </div>

            <div className="mt-2 text-xs text-amber-600">
              <div className="flex items-center space-x-1">
                <DocumentIcon className="h-3 w-3" />
                <span>Черновик доступен в разделе восстановления</span>
              </div>
            </div>
          </div>
        </div>
      </Alert>
    </div>
  );
};

export default DraftSavedNotification;