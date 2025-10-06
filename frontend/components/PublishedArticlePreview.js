import React, { useState, useEffect } from 'react';

const PublishedArticlePreview = ({ draftId, isOpen, onClose }) => {
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && draftId) {
      fetchArticleContent();
    }
  }, [isOpen, draftId]);

  const fetchArticleContent = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/proxy/news-generation/published/${draftId}`, {
        credentials: 'include'
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Ошибка загрузки статьи');
      }

      setArticle(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContent = async () => {
    if (article?.content) {
      try {
        await navigator.clipboard.writeText(article.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy content:', err);
      }
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Неизвестно';
    return new Date(dateString).toLocaleString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl transform transition-all duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <h2 className="text-xl font-bold text-gray-900">
              Предварительный просмотр публикации
            </h2>
          </div>

          <div className="flex items-center space-x-2">
            {article?.content && (
              <button
                onClick={handleCopyContent}
                className="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                title="Копировать HTML"
              >
                {copied ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
                <span>{copied ? 'Скопировано!' : 'Копировать HTML'}</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <span className="ml-2 text-gray-600">Загрузка статьи...</span>
            </div>
          )}

          {error && (
            <div className="p-6 text-center">
              <div className="text-red-600 mb-2">❌ Ошибка загрузки</div>
              <div className="text-gray-600 text-sm">{error}</div>
            </div>
          )}

          {article && !loading && !error && (
            <div className="p-6">
              {/* Article Info */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center space-x-2">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span className="text-gray-600">Опубликовано:</span>
                    <span className="font-medium">{formatDate(article.published_at)}</span>
                  </div>

                  {article.published_project && (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-purple-500 rounded-full"></div>
                      <span className="text-gray-600">Проект:</span>
                      <span className="font-medium">{article.published_project}</span>
                    </div>
                  )}

                  {article.bitrix_id && (
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      <span className="text-gray-600">ID в Bitrix:</span>
                      <span className="font-medium">#{article.bitrix_id}</span>
                    </div>
                  )}

                  {article.seo_description && (
                    <div className="md:col-span-2">
                      <span className="text-gray-600">SEO описание:</span>
                      <div className="mt-1 text-sm text-gray-800 italic">"{article.seo_description}"</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Article Title */}
              <h1 className="text-2xl font-bold text-gray-900 mb-6 leading-tight">
                {article.title}
              </h1>

              {/* Article Image */}
              {article.image_url && (
                <div className="mb-6">
                  <img
                    src={article.image_url}
                    alt="Article"
                    className="w-full max-w-md mx-auto rounded-lg shadow-md"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Article Content */}
              <div className="prose max-w-none">
                <div
                  className="medical-article"
                  dangerouslySetInnerHTML={{ __html: article.content }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PublishedArticlePreview;