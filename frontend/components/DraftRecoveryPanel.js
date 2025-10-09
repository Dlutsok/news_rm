import React, { useState, useEffect } from 'react';
import {
  XIcon,
  ClockIcon,
  WarningIcon,
  DocumentIcon,
  RefreshIcon
} from './ui/icons';
import apiClient from '@utils/api';
import Alert from '@components/ui/Alert';
import Button from '@components/ui/Button';
import Card from '@components/ui/Card';

const DraftRecoveryPanel = ({ onDraftRecovered }) => {
  const [failedDrafts, setFailedDrafts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [retrying, setRetrying] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFailedDrafts();
  }, []);

  const loadFailedDrafts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.request('/api/news-generation/failed-drafts?limit=20&include_recoverable_only=true', {
        method: 'GET'
      });
      setFailedDrafts(data);
    } catch (err) {
      console.error('Error loading failed drafts:', err);
      setError('Ошибка загрузки черновиков с ошибками');
    } finally {
      setLoading(false);
    }
  };

  const retryDraft = async (draftId) => {
    try {
      setRetrying(prev => ({ ...prev, [draftId]: true }));
      setError(null);

      const data = await apiClient.request(`/api/news-generation/retry/${draftId}`, {
        method: 'POST'
      });

      if (data.success) {
        // Убираем черновик из списка ошибочных
        setFailedDrafts(prev => prev.filter(draft => draft.id !== draftId));

        // Уведомляем родительский компонент о восстановлении
        if (onDraftRecovered) {
          onDraftRecovered(draftId, data);
        }

        // Показываем успешное сообщение
        alert(`Черновик #${draftId} успешно восстановлен!`);
      }
    } catch (err) {
      console.error('Error retrying draft:', err);
      setError(`Ошибка восстановления черновика #${draftId}: ${err.message}`);
    } finally {
      setRetrying(prev => ({ ...prev, [draftId]: false }));
    }
  };

  const removeDraft = async (draftId) => {
    try {
      await apiClient.request(`/api/news-generation/clear-error/${draftId}`, {
        method: 'DELETE'
      });
      setFailedDrafts(prev => prev.filter(draft => draft.id !== draftId));
    } catch (err) {
      console.error('Error removing draft from recovery list:', err);
      setError(`Ошибка удаления черновика #${draftId} из списка восстановления`);
    }
  };

  const formatErrorStep = (step) => {
    const stepNames = {
      'summary': 'Создание выжимки',
      'generation': 'Генерация статьи',
      'publication': 'Публикация',
      'image_generation': 'Генерация изображения'
    };
    return stepNames[step] || step;
  };

  const formatTimeAgo = (date) => {
    if (!date) return '';
    const now = new Date();
    const errorTime = new Date(date);
    const diffMs = now - errorTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays} дн. назад`;
    if (diffHours > 0) return `${diffHours} ч. назад`;
    if (diffMins > 0) return `${diffMins} мин. назад`;
    return 'только что';
  };

  if (loading) {
    return (
      <Card className="p-4">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full w-4 h-4 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-600">Загрузка черновиков...</span>
        </div>
      </Card>
    );
  }

  if (failedDrafts.length === 0) {
    return null; // Не показываем панель, если нет ошибочных черновиков
  }

  return (
    <Card className="mb-6">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <WarningIcon className="w-5 h-5 text-yellow-500" />
            <h3 className="text-lg font-medium text-gray-900">
              Черновики с ошибками ({failedDrafts.length})
            </h3>
          </div>
          <Button
            onClick={loadFailedDrafts}
            variant="outline"
            size="sm"
            disabled={loading}
          >
            Обновить
          </Button>
        </div>
        <p className="mt-1 text-sm text-gray-600">
          Черновики, которые можно восстановить после ошибок
        </p>
      </div>

      {error && (
        <div className="p-4">
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="divide-y divide-gray-200">
        {failedDrafts.map((draft) => (
          <div key={draft.id} className="p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <DocumentIcon className="w-4 h-4 text-gray-400" />
                  <h4 className="text-sm font-medium text-gray-900">
                    Черновик #{draft.id}
                  </h4>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                    {formatErrorStep(draft.last_error_step)}
                  </span>
                </div>

                <div className="mt-1 text-sm text-gray-600">
                  <p className="truncate">{draft.summary}</p>
                </div>

                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <ClockIcon className="h-3 w-3" />
                    <span>{formatTimeAgo(draft.last_error_at)}</span>
                  </div>
                  <span>Попыток: {draft.retry_count}/3</span>
                  <span>Проект: {draft.project}</span>
                </div>

                {draft.last_error_message && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                    {draft.last_error_message}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2 ml-4">
                <Button
                  onClick={() => retryDraft(draft.id)}
                  disabled={!draft.can_retry || retrying[draft.id]}
                  size="sm"
                  variant="primary"
                  className="flex items-center space-x-1"
                >
                  <RefreshIcon className={`h-3 w-3 ${retrying[draft.id] ? 'animate-spin' : ''}`} />
                  <span>{retrying[draft.id] ? 'Восстановление...' : 'Восстановить'}</span>
                </Button>

                <Button
                  onClick={() => removeDraft(draft.id)}
                  size="sm"
                  variant="ghost"
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XIcon className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-600">
          Черновики автоматически сохраняются при ошибках и могут быть восстановлены в любое время.
          Максимум 3 попытки восстановления на черновик.
        </p>
      </div>
    </Card>
  );
};

export default DraftRecoveryPanel;