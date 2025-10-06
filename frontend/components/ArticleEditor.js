import React, { useState, useEffect, useMemo, useRef } from 'react';
import { FaExpand, FaCompress, FaTag } from 'react-icons/fa';
import {
  SaveIcon,
  ViewIcon,
  XIcon,
  LoadingIcon,
  GlobalIcon,
  WarningIcon,
  ClockIcon,
  NewsIcon,
  ImageIcon
} from './ui/icons';
import dynamic from 'next/dynamic';
import AutoSaveIndicator from './AutoSaveIndicator';
import useAutoSaveDraft from '@utils/useAutoSaveDraft';

// Динамический импорт ReactQuill для избежания SSR проблем
const ReactQuill = dynamic(() => import('react-quill'), { 
  ssr: false,
  loading: () => <div className="h-80 bg-gray-100 rounded animate-pulse flex items-center justify-center">
    <LoadingIcon className="animate-spin text-gray-400" />
  </div>
});

const ArticleEditor = ({ 
  isOpen, 
  onClose, 
  articleData, 
  onSave, 
  onPreview,
  onRegenerateImage,
  onPublish,
  publishLabel,
  isLoading = false,
  isPublishing = false
}) => {
  const [formData, setFormData] = useState({
    news_text: '',
    seo_title: '',
    seo_description: '',
    seo_keywords: [],
    image_prompt: '',
    image_url: ''
  });
  
  const [keywordInput, setKeywordInput] = useState('');
  const [isRegeneratingImage, setIsRegeneratingImage] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const lastSavedRef = useRef(null);
  const editorContainerRef = useRef(null);

  // Интеграция с автосохранением
  const draftId = articleData?.draft_id || articleData?.id;
  const { saveDraft, saving, error: saveError, lastSaved } = useAutoSaveDraft(draftId, articleData);

  // Конфигурация для ReactQuill - расширенная для медицинских статей
  const quillModules = useMemo(() => ({
    toolbar: [
      [{ 'header': [2, 3, false] }],  // H2, H3 для медицинских разделов
      ['bold', 'italic', 'underline'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      [{ 'indent': '-1'}, { 'indent': '+1' }],
      ['link', 'blockquote'],
      [{ 'align': [] }],
      ['clean']
    ],
  }), []);

  const quillFormats = [
    'header', 'bold', 'italic', 'underline',
    'list', 'bullet', 'indent', 'link', 'blockquote', 'align'
  ];

  // Функция для обработки HTML контента от GPT
  const processGptHtml = (html) => {
    if (!html) return '';

    // Если контент уже содержит HTML теги, используем как есть
    if (html.includes('<p>') || html.includes('<h2>') || html.includes('<h3>')) {
      return html;
    }

    // Если это старый формат с \n\n, конвертируем в HTML
    return html
      .split('\n\n')
      .filter(paragraph => paragraph.trim())
      .map(paragraph => `<p>${paragraph.trim()}</p>`)
      .join('');
  };

  // Утилиты: получение plain-text, подсчёты, валидации
  const getPlainText = (html) => {
    if (!html) return '';
    const tmp = typeof window !== 'undefined' ? document.createElement('div') : null;
    if (!tmp) return html;
    tmp.innerHTML = html;
    return (tmp.textContent || tmp.innerText || '').trim();
  };

  const computeStats = (html, title, description, keywordsArr) => {
    const plain = getPlainText(html);
    const charCount = plain.length;
    const wordCount = plain.split(/\s+/).filter(Boolean).length;
    const readingTimeMin = Math.max(1, Math.round(wordCount / 200));
    return {
      charCount,
      wordCount,
      readingTimeMin,
      titleLen: (title || '').length,
      descLen: (description || '').length,
      keywordsCount: (keywordsArr || []).length,
    };
  };

  const getLenBadgeClass = (len, min, max) => {
    if (typeof min === 'number' && len < min) return 'text-red-600';
    if (typeof max === 'number' && len > max) return 'text-amber-600';
    return 'text-green-600';
  };

  useEffect(() => {
    if (articleData) {
      // Обрабатываем контент от GPT (HTML или старый формат с \n)
      // Поддерживаем как старый формат (news_text), так и новый (generated_news_text)
      const newsText = articleData.news_text || articleData.generated_news_text || '';
      const formattedNewsText = processGptHtml(newsText);

      // Парсим keywords если они приходят как JSON строка
      let keywords = [];
      const keywordsData = articleData.seo_keywords || articleData.generated_seo_keywords;
      if (typeof keywordsData === 'string') {
        try {
          keywords = JSON.parse(keywordsData);
        } catch (e) {
          keywords = keywordsData.split(',').map(k => k.trim()).filter(Boolean);
        }
      } else if (Array.isArray(keywordsData)) {
        keywords = keywordsData;
      }

      setFormData({
        news_text: formattedNewsText,
        seo_title: articleData.seo_title || articleData.generated_seo_title || '',
        seo_description: articleData.seo_description || articleData.generated_seo_description || '',
        seo_keywords: keywords,
        image_prompt: articleData.image_prompt || articleData.generated_image_prompt || '',
        image_url: articleData.image_url || articleData.generated_image_url || ''
      });
      setKeywordInput(keywords.join(', '));
      lastSavedRef.current = {
        news_text: formattedNewsText,
        seo_title: articleData.seo_title || articleData.generated_seo_title || '',
        seo_description: articleData.seo_description || articleData.generated_seo_description || '',
        seo_keywords: keywords,
        image_prompt: articleData.image_prompt || articleData.generated_image_prompt || '',
        image_url: articleData.image_url || articleData.generated_image_url || ''
      };
      setHasChanges(false);
    }
  }, [articleData]);

  if (!isOpen) return null;

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Отслеживаем наличие изменений
    const draft = {
      ...formData,
      [field]: value,
      seo_keywords: field === 'seo_keywords' ? value : formData.seo_keywords,
    };
    setHasChanges(JSON.stringify(draft) !== JSON.stringify(lastSavedRef.current));
  };

  const handleKeywordsChange = (value) => {
    setKeywordInput(value);
    const keywords = value.split(',').map(k => k.trim()).filter(k => k);
    setFormData(prev => ({
      ...prev,
      seo_keywords: keywords
    }));
    const draft = { ...formData, seo_keywords: keywords, }; 
    setHasChanges(JSON.stringify(draft) !== JSON.stringify(lastSavedRef.current));
  };

  // Функция для очистки и нормализации HTML
  const cleanHtmlFormatting = (html) => {
    if (!html) return '';

    // Нормализуем HTML от ReactQuill, сохраняя медицинскую структуру
    return html
      .replace(/<div><br><\/div>/g, '')      // Убираем пустые div
      .replace(/<div>/g, '<p>')              // Заменяем div на p
      .replace(/<\/div>/g, '</p>')           // Заменяем /div на /p
      .replace(/<p><\/p>/g, '')              // Убираем пустые параграфы
      .replace(/<p><br><\/p>/g, '')          // Убираем параграфы только с br
      .replace(/(<br\s*\/?>){2,}/g, '<br>')  // Ограничиваем множественные br
      .replace(/\s+/g, ' ')                  // Нормализуем пробелы
      .trim();
  };

  const handleSave = async () => {
    try {
      // Очищаем и нормализуем HTML перед сохранением
      const dataToSave = {
        ...formData,
        news_text: cleanHtmlFormatting(formData.news_text)
      };

      // Используем автосохранение если есть draftId, иначе обычное сохранение
      if (draftId && saveDraft) {
        await saveDraft(dataToSave);
      } else {
        await onSave(dataToSave);
      }

      lastSavedRef.current = dataToSave;
      setHasChanges(false);

      // Показываем сообщение об успешном сохранении
      alert('Черновик успешно сохранён!');
    } catch (error) {
      console.error('Ошибка при сохранении:', error);
      alert('Ошибка при сохранении черновика: ' + error.message);
    }
  };

  const handlePreview = () => {
    // Очищаем HTML для предпросмотра
    const dataToPreview = {
      ...formData,
      news_text: cleanHtmlFormatting(formData.news_text)
    };
    onPreview(dataToPreview);
  };

  const handlePublish = () => {
    // Очищаем HTML для публикации
    const dataToPublish = {
      ...formData,
      news_text: cleanHtmlFormatting(formData.news_text)
    };
    onPublish(dataToPublish);
  };

  const handleRegenerateImage = async () => {
    if (!formData.image_prompt.trim()) {
      alert('Введите описание для генерации изображения');
      return;
    }

    // Проверяем что onRegenerateImage передан
    if (typeof onRegenerateImage !== 'function') {
      alert('Функция генерации изображения недоступна');
      return;
    }

    setIsRegeneratingImage(true);
    try {
      // Родитель обновит articleData.image_url; локально ждём синхронизации через useEffect
      await onRegenerateImage(formData.image_prompt);
    } catch (error) {
      console.error('Error regenerating image:', error);
      alert('Ошибка при генерации изображения');
    } finally {
      setIsRegeneratingImage(false);
    }
  };

  const openImageInNewTab = (imageUrl) => {
    if (imageUrl) {
      window.open(imageUrl, '_blank', 'noopener,noreferrer');
    }
  };

  // Горячие клавиши: Cmd/Ctrl+S для сохранения, Esc — закрыть
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (!isLoading) handleSave();
      }
      if (e.key === 'Escape') {
        if (!isLoading) onClose();
      }
    }
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isLoading, formData]);

  const stats = computeStats(formData.news_text, formData.seo_title, formData.seo_description, formData.seo_keywords);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998]">
      <div ref={editorContainerRef} className={`bg-white rounded border border-gray-300 w-full mx-4 overflow-y-auto ${
        isFullscreen
          ? 'max-w-none h-full max-h-full m-0 rounded-none'
          : 'max-w-6xl max-h-[95vh]'
      }`}>
        {/* Sticky header */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200">
          <div className="px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-gray-900">Редактирование статьи</h2>
              <AutoSaveIndicator
                data={formData}
                onSave={draftId ? saveDraft : onSave}
                saveInterval={30000}
                disabled={isLoading || isPublishing}
              />
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden md:flex items-center text-sm text-gray-500 mr-3">
                <ClockIcon className="mr-1" /> {stats.readingTimeMin} мин чтения
              </div>
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="text-gray-500 hover:text-gray-700 transition-colors p-2 rounded-lg hover:bg-gray-100"
                disabled={isLoading}
                title={isFullscreen ? "Выйти из полноэкранного режима" : "Полноэкранный режим"}
              >
                {isFullscreen ? <FaCompress  /> : <FaExpand  />}
              </button>
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 transition-colors p-2 rounded-lg hover:bg-gray-100"
                disabled={isLoading}
                title="Закрыть"
              >
                <XIcon  />
              </button>
            </div>
          </div>

        </div>

        <div className="p-4">
          <>
          {isFullscreen ? (
            // Полноэкранный режим - оптимизированная компоновка
            <div className="h-full flex flex-col">
              {/* Основная область редактирования */}
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
                {/* Колонка 1: Текст статьи */}
                <div className="lg:col-span-2 flex flex-col">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Текст статьи
                  </label>
                  <div className="flex-1 border border-gray-300 rounded overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
                    <ReactQuill
                      theme="snow"
                      value={formData.news_text}
                      onChange={(value) => handleInputChange('news_text', value)}
                      modules={quillModules}
                      formats={quillFormats}
                      placeholder="Введите текст статьи..."
                      className="quill-editor h-full"
                      style={{ height: 'calc(100vh - 180px)' }}
                    />
                  </div>
                </div>

                {/* Колонка 2: SEO поля и изображение */}
                <div className="space-y-4">
                  {/* SEO Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      SEO Заголовок
                    </label>
                    <input
                      type="text"
                      value={formData.seo_title}
                      onChange={(e) => handleInputChange('seo_title', e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="SEO заголовок..."
                    />
                    <p className={`text-sm mt-1 ${getLenBadgeClass(stats.titleLen, 10, 60)}`}>
                      Длина заголовка: {stats.titleLen}/60
                    </p>
                  </div>

                  {/* SEO Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      SEO Описание
                    </label>
                    <textarea
                      value={formData.seo_description}
                      onChange={(e) => handleInputChange('seo_description', e.target.value)}
                      className="w-full min-h-20 max-h-32 p-2 border border-gray-300 rounded resize-y overflow-auto focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="SEO описание..."
                    />
                    <p className={`text-sm mt-1 ${getLenBadgeClass(stats.descLen, 50, 160)}`}>
                      Длина описания: {stats.descLen}/160
                    </p>
                  </div>

                  {/* SEO Keywords */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      SEO Ключевые слова
                    </label>
                    <input
                      type="text"
                      value={keywordInput}
                      onChange={(e) => handleKeywordsChange(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Ключевые слова..."
                    />
                    <div className="flex flex-wrap gap-1 mt-2 max-h-20 overflow-y-auto">
                      {formData.seo_keywords.map((keyword, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded text-xs inline-flex items-center gap-1"
                        >
                          <FaTag  /> {keyword}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Изображение */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Изображение
                    </label>
                    <div className="border border-gray-300 rounded overflow-hidden h-32">
                      {formData.image_url ? (
                        <img
                          src={formData.image_url}
                          alt="Article"
                          className="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
                          onClick={() => openImageInNewTab(formData.image_url)}
                          title="Нажмите, чтобы открыть в новой вкладке"
                        />
                      ) : (
                        <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                          <ImageIcon className="w-6 h-6 text-gray-400" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Image Prompt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Описание для изображения
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={formData.image_prompt}
                        onChange={(e) => handleInputChange('image_prompt', e.target.value)}
                        className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Описание изображения..."
                      />
                      {typeof onRegenerateImage === 'function' && (
                        <button
                          onClick={handleRegenerateImage}
                          disabled={isRegeneratingImage || !formData.image_prompt.trim()}
                          className="px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
                        >
                          {isRegeneratingImage ? (
                            <LoadingIcon className="animate-spin" />
                          ) : (
                            <ImageIcon />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Статистика */}
                  <div className="bg-gray-50 rounded p-3">
                    <h4 className="font-medium text-gray-700 mb-2 text-sm">Статистика</h4>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span>Символов:</span>
                        <span className={`font-medium ${stats.charCount >= 2000 ? 'text-green-600' : 'text-red-600'}`}>
                          {stats.charCount}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Слов:</span>
                        <span className="font-medium">{stats.wordCount}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Чтение:</span>
                        <span className="font-medium">{stats.readingTimeMin} мин</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Обычный режим - двухколоночная компоновка
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column - Content */}
              <div className="space-y-6">
                {/* Article Text */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Текст статьи
                  </label>
                  <div className="border border-gray-300 rounded overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent">
                    <ReactQuill
                      theme="snow"
                      value={formData.news_text}
                      onChange={(value) => handleInputChange('news_text', value)}
                      modules={quillModules}
                      formats={quillFormats}
                      placeholder="Введите текст статьи..."
                      className="quill-editor"
                      style={{ height: '450px' }}
                    />
                  </div>
                </div>

                {/* SEO Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SEO Заголовок
                  </label>
                  <input
                    type="text"
                    value={formData.seo_title}
                    onChange={(e) => handleInputChange('seo_title', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Введите SEO заголовок..."
                  />
                  <p className={`text-sm mt-1 ${getLenBadgeClass(stats.titleLen, 10, 60)}`}>
                    Длина заголовка: {stats.titleLen}/60
                  </p>
                </div>

                {/* SEO Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SEO Описание
                  </label>
                  <textarea
                    value={formData.seo_description}
                    onChange={(e) => handleInputChange('seo_description', e.target.value)}
                    className="w-full min-h-24 max-h-80 p-2 border border-gray-300 rounded resize-y overflow-auto focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-2"
                    placeholder="Введите SEO описание..."
                  />
                  <p className={`text-sm mt-1 ${getLenBadgeClass(stats.descLen, 50, 160)}`}>
                    Длина описания: {stats.descLen}/160
                  </p>
                </div>

                {/* SEO Keywords */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SEO Ключевые слова
                  </label>
                  <input
                    type="text"
                    value={keywordInput}
                    onChange={(e) => handleKeywordsChange(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Введите ключевые слова через запятую..."
                  />
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.seo_keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded text-sm inline-flex items-center gap-1"
                      >
                        <FaTag /> {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

            {/* Right Column - Image */}
            <div className="space-y-6">
              {/* Image Preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Изображение
                </label>
                <div className="border border-gray-300 rounded overflow-hidden">
                  {formData.image_url ? (
                    <div className="relative group">
                      <img
                        src={formData.image_url}
                        alt="Article"
                        className="w-full h-64 object-cover cursor-pointer hover:opacity-90 transition-opacity"
                        onClick={() => openImageInNewTab(formData.image_url)}
                        title="Нажмите, чтобы открыть в новой вкладке"
                      />
                    </div>
                  ) : (
                    <div className="w-full h-64 bg-gray-100 flex items-center justify-center">
                      <ImageIcon className="w-10 h-10 text-gray-400" />
                    </div>
                  )}
                </div>
              </div>

              {/* Image Prompt */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Описание для изображения
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={formData.image_prompt}
                    onChange={(e) => handleInputChange('image_prompt', e.target.value)}
                    className="flex-1 p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Описание изображения..."
                  />
                  {typeof onRegenerateImage === 'function' && (
                    <button
                      onClick={handleRegenerateImage}
                      disabled={isRegeneratingImage || !formData.image_prompt.trim()}
                      className="px-3 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
                    >
                      {isRegeneratingImage ? (
                        <LoadingIcon className="animate-spin" />
                      ) : (
                        <ImageIcon />
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Statistics */}
              <div className="bg-gray-50 rounded p-4">
                <h4 className="font-medium text-gray-700 mb-3">Статистика</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Символов в тексте:</span>
                    <span className={`font-medium ${stats.charCount >= 2000 ? 'text-green-600' : 'text-red-600'}`}>
                      {stats.charCount}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Слов в тексте:</span>
                    <span className="font-medium">{stats.wordCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ключевых слов:</span>
                    <span className="font-medium">{stats.keywordsCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Время чтения:</span>
                    <span className="font-medium">~ {stats.readingTimeMin} мин</span>
                  </div>
                  {formData.news_text.length < 2000 && (
                    <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-xs">
                      ⚠️ Рекомендуется минимум 2000 символов для хорошего SEO
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          )}
          </>

          {/* Action Buttons для новости */}
          <div className="flex justify-end gap-3 pt-4 mt-4 border-t">
            <button
              onClick={handleSave}
              disabled={isLoading || isPublishing || saving || !formData.news_text.trim() || !formData.seo_title.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <SaveIcon  />
              {(isLoading || saving) ? 'Сохранение...' : 'Сохранить'}
            </button>

            {onPublish && (
              <button
                onClick={handlePublish}
                disabled={isLoading || isPublishing || saving || !formData.news_text.trim() || !formData.seo_title.trim()}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <GlobalIcon  />
                {isPublishing ? 'Публикация...' : (typeof publishLabel === 'string' ? publishLabel : 'Опубликовать')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticleEditor;
