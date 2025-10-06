import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const useAutoSaveDraft = (draftId, initialData = null) => {
  const [draft, setDraft] = useState(initialData);
  const [loading, setLoading] = useState(!initialData);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [lastSaved, setLastSaved] = useState(null);

  // Загружаем черновик если не передан начальный
  useEffect(() => {
    if (!initialData && draftId) {
      loadDraft();
    }
  }, [draftId, initialData]);

  const loadDraft = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`/api/news-generation/drafts/${draftId}`);
      setDraft(response.data);
    } catch (err) {
      console.error('Error loading draft:', err);
      setError('Ошибка загрузки черновика');
    } finally {
      setLoading(false);
    }
  };

  const saveDraft = useCallback(async (draftData) => {
    if (!draftId) {
      throw new Error('Draft ID is required for saving');
    }

    try {
      setSaving(true);
      setError(null);

      const updateData = {
        news_text: draftData.generated_news_text || draftData.news_text || '',
        seo_title: draftData.generated_seo_title || draftData.seo_title || '',
        seo_description: draftData.generated_seo_description || draftData.seo_description || '',
        seo_keywords: Array.isArray(draftData.generated_seo_keywords)
          ? draftData.generated_seo_keywords
          : (draftData.seo_keywords || []),
        image_prompt: draftData.generated_image_prompt || draftData.image_prompt || '',
        image_url: draftData.generated_image_url || draftData.image_url || ''
      };

      const response = await axios.put(`/api/news-generation/drafts/${draftId}`, updateData);

      setLastSaved(new Date());
      setDraft(prev => ({ ...prev, ...response.data }));

      return response.data;
    } catch (err) {
      console.error('Error saving draft:', err);
      const errorMessage = err.response?.data?.detail || 'Ошибка сохранения черновика';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setSaving(false);
    }
  }, [draftId]);

  const updateDraft = useCallback((updates) => {
    setDraft(prev => ({ ...prev, ...updates }));
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const retryLastOperation = useCallback(async () => {
    if (!draftId) return null;

    try {
      setError(null);
      const response = await axios.post(`/api/news-generation/retry/${draftId}`);

      if (response.data.success) {
        // Перезагружаем черновик после успешного восстановления
        await loadDraft();
      }

      return response.data;
    } catch (err) {
      console.error('Error retrying draft operation:', err);
      const errorMessage = err.response?.data?.detail || 'Ошибка восстановления операции';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, [draftId]);

  const canRetry = draft?.can_retry && draft?.retry_count < 3;

  return {
    draft,
    loading,
    saving,
    error,
    lastSaved,
    canRetry,
    saveDraft,
    updateDraft,
    loadDraft,
    clearError,
    retryLastOperation
  };
};

export default useAutoSaveDraft;