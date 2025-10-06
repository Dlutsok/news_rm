import React, { useState, useEffect, useCallback } from 'react';
import { FaTelegram, FaCopy, FaRocket, FaComments } from 'react-icons/fa';
import {
  LoadingIcon,
  ActionIcon,
  ViewIcon,
  XIcon
} from './ui/icons';
import { HiEye } from 'react-icons/hi';

const TelegramPostEditor = ({
  draftId, // Для старой логики (draft-based)
  newsId, // ID опубликованной новости (новая логика)
  newsData, // Данные опубликованной новости
  isLoading = false,
  onGenerate,
  onPostSaved, // Callback при сохранении поста
  existingPost = null, // Существующий пост для редактирования
  isOpen = false, // Модальное окно
  onClose, // Закрытие модального окна
  articleData // Для backward compatibility
}) => {
  const [telegramPost, setTelegramPost] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [articleUrl, setArticleUrl] = useState('');
  const [linkButtonText, setLinkButtonText] = useState('📖 Читать полную статью');
  const [isPublishing, setIsPublishing] = useState(false);
  const [savedPostId, setSavedPostId] = useState(null);

  // Настройки поста
  const [postSettings, setPostSettings] = useState({
    hook_type: 'question', // 'question', 'shocking_fact', 'statistics', 'contradiction'
    disclosure_level: 'hint', // 'hint', 'main_idea', 'almost_all'
    call_to_action: 'curiosity', // 'curiosity', 'urgency', 'expertise'
    include_image: true
  });

  // Загрузка существующего поста при редактировании
  useEffect(() => {
    if (existingPost) {
      setTelegramPost(existingPost.post_text);
      setPostSettings({
        hook_type: existingPost.hook_type,
        disclosure_level: existingPost.disclosure_level,
        call_to_action: existingPost.call_to_action,
        include_image: existingPost.include_image
      });
    }
  }, [existingPost]);

  // Инициализация URL из данных новости
  useEffect(() => {
    if (newsData && newsData.published_url) {
      setArticleUrl(newsData.published_url);
    }
  }, [newsData]);

  // Стабильный обработчик изменения текста
  const handleTextChange = useCallback((e) => {
    setTelegramPost(e.target.value);
  }, []);

  const handleGenerate = async () => {
    if (!newsId && !draftId) {
      alert('Отсутствуют данные для генерации поста');
      return;
    }

    setIsGenerating(true);
    try {
      // Новая логика для опубликованных новостей
      if (newsId && newsData) {
        const response = await fetch(`/api/telegram-posts/news/${newsId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            hook_type: postSettings.hook_type,
            disclosure_level: postSettings.disclosure_level,
            call_to_action: postSettings.call_to_action,
            include_image: postSettings.include_image,
            article_url: articleUrl
          })
        });

        const data = await response.json();

        if (response.ok) {
          setTelegramPost(data.post_text);
          if (onGenerate) {
            onGenerate(data.post_text);
          }
        } else {
          throw new Error(data.detail || 'Ошибка генерации поста');
        }
      }
      // Старая логика для draft-based (для backward compatibility)
      else if (draftId) {
        const response = await fetch(`/api/news-generation/generate-telegram-post/${draftId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            settings: postSettings
          })
        });

        const data = await response.json();

        if (data.success) {
          setTelegramPost(data.telegram_post);
          if (onGenerate) {
            onGenerate(data.telegram_post);
          }
        } else {
          throw new Error(data.detail || 'Ошибка генерации поста');
        }
      }
    } catch (error) {
      console.error('Error generating Telegram post:', error);
      alert('Ошибка генерации поста: ' + error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!telegramPost.trim()) {
      alert('Пост не может быть пустым');
      return null;
    }

    if (!newsId) {
      alert('Отсутствуют данные новости для сохранения поста');
      return null;
    }

    try {
      setIsGenerating(true);

      const response = await fetch(`/api/telegram-posts/news/${newsId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          hook_type: postSettings.hook_type,
          disclosure_level: postSettings.disclosure_level,
          call_to_action: postSettings.call_to_action,
          include_image: postSettings.include_image,
          article_url: articleUrl
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSavedPostId(data.id);
        alert('Telegram пост успешно сохранен!');
        if (onPostSaved) {
          onPostSaved(data);
        }
        if (onClose) {
          onClose();
        }
        return data.id; // Возвращаем ID поста
      } else {
        throw new Error(data.detail || 'Ошибка сохранения поста');
      }
    } catch (error) {
      console.error('Error saving Telegram post:', error);
      alert('Ошибка сохранения поста: ' + error.message);
      return null;
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(telegramPost);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handlePublish = async () => {
    if (!telegramPost.trim()) {
      alert('Нет текста поста для публикации');
      return;
    }

    if (!newsId && !existingPost) {
      alert('Нет данных для публикации поста');
      return;
    }

    try {
      setIsPublishing(true);

      // Сначала сохраняем пост, если он еще не сохранен
      let postId = existingPost ? existingPost.id : savedPostId;

      if (!postId) {
        postId = await handleSave();
      }

      if (!postId) {
        throw new Error('Не удалось получить ID поста для публикации');
      }

      // Затем публикуем в Telegram
      const response = await fetch(`/api/telegram-posts/${postId}/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          post_text: telegramPost,
          article_url: articleUrl,
          link_button_text: linkButtonText
        })
      });

      const data = await response.json();

      if (response.ok) {
        alert('Пост успешно опубликован в Telegram!');
        if (onPostSaved) {
          onPostSaved(data);
        }
      } else {
        throw new Error(data.detail || 'Ошибка публикации поста');
      }
    } catch (error) {
      console.error('Error publishing to Telegram:', error);
      alert('Ошибка публикации: ' + error.message);
    } finally {
      setIsPublishing(false);
    }
  };

  const getCharCount = () => {
    return telegramPost.length;
  };

  const getCharCountClass = () => {
    const count = getCharCount();
    const minLength = 200;
    const maxLength = 350;

    if (count < minLength) return 'text-amber-600';
    if (count > maxLength) return 'text-red-600';
    return 'text-green-600';
  };

  const insertEmoji = (emoji) => {
    const textarea = document.getElementById('telegram-post-textarea');
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newText = telegramPost.substring(0, start) + emoji + telegramPost.substring(end);
      setTelegramPost(newText);
      // Восстанавливаем позицию курсора
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + emoji.length, start + emoji.length);
      }, 0);
    } else {
      setTelegramPost(telegramPost + emoji);
    }
  };

  // Популярные эмодзи для медицинских постов
  const medicalEmojis = [
    '🩺', '💊', '🧬', '🔬', '🧪', '🩻', '🫀', '🧠',
    '💉', '🏥', '👩‍⚕️', '👨‍⚕️', '📊', '📈', '⚕️', '🔍',
    '😊', '👍', '💪', '✨', '🎯', '📝', '💯', '🙏'
  ];

  // Функция для парсинга форматированного текста (Markdown-style)
  const parseFormattedText = (text) => {
    if (!text) return null;

    // Разбиваем текст на строки
    const lines = text.split('\n');

    return lines.map((line, lineIndex) => {
      // Обрабатываем пустые строки
      if (line.trim() === '') {
        return <div key={lineIndex} className="h-4">&nbsp;</div>;
      }

      // Парсим форматирование в строке
      const parts = [];
      let currentText = '';
      let inBold = false;
      let inItalic = false;
      let inStrikethrough = false;
      let inCode = false;
      let i = 0;

      while (i < line.length) {
        const char = line[i];
        const nextChar = line[i + 1] || '';

        // Проверяем на начало/конец форматирования
        if (char === '*' && nextChar === '*') {
          // Жирный текст **
          if (currentText) {
            parts.push({ text: currentText, bold: inBold, italic: inItalic, strikethrough: inStrikethrough, code: inCode });
            currentText = '';
          }
          inBold = !inBold;
          i += 2;
          continue;
        } else if (char === '*' && nextChar !== '*') {
          // Курсив *
          if (currentText) {
            parts.push({ text: currentText, bold: inBold, italic: inItalic, strikethrough: inStrikethrough, code: inCode });
            currentText = '';
          }
          inItalic = !inItalic;
          i += 1;
          continue;
        } else if (char === '~' && nextChar === '~') {
          // Зачеркнутый текст ~~
          if (currentText) {
            parts.push({ text: currentText, bold: inBold, italic: inItalic, strikethrough: inStrikethrough, code: inCode });
            currentText = '';
          }
          inStrikethrough = !inStrikethrough;
          i += 2;
          continue;
        } else if (char === '`') {
          // Код `
          if (currentText) {
            parts.push({ text: currentText, bold: inBold, italic: inItalic, strikethrough: inStrikethrough, code: inCode });
            currentText = '';
          }
          inCode = !inCode;
          i += 1;
          continue;
        } else {
          currentText += char;
          i += 1;
        }
      }

      // Добавляем оставшийся текст
      if (currentText) {
        parts.push({ text: currentText, bold: inBold, italic: inItalic, strikethrough: inStrikethrough, code: inCode });
      }

      // Создаем JSX для строки
      const lineContent = parts.map((part, partIndex) => {
        let className = '';
        if (part.bold) className += ' font-bold';
        if (part.italic) className += ' italic';
        if (part.strikethrough) className += ' line-through';
        if (part.code) className += ' font-mono bg-gray-100 px-1 rounded text-sm';

        return (
          <span key={partIndex} className={className.trim()}>
            {part.text}
          </span>
        );
      });

      return (
        <div key={lineIndex}>
          {lineContent}
        </div>
      );
    });
  };

  // Если используется как модальное окно
  if (isOpen) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
        <div className="bg-white rounded-lg shadow-xl w-full mx-4 max-w-7xl max-h-[95vh] overflow-y-auto">
          {/* Header модального окна */}
          <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FaTelegram className="text-blue-500 w-5 h-5" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {existingPost ? 'Редактирование Telegram поста' : 'Создание Telegram поста'}
                </h2>
                <p className="text-sm text-gray-600">
                  {newsData?.seo_title ? `${newsData.seo_title.substring(0, 60)}...` : 'Интригующий анонс для канала'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors p-2 rounded-lg hover:bg-gray-100"
              title="Закрыть"
            >
              <XIcon  />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <TelegramPostEditorContent />
          </div>
        </div>
      </div>
    );
  }

  // Встроенный режим (старая логика)
  function TelegramPostEditorContent() {
    return (
      <div className="space-y-6">
        {/* Заголовок секции */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FaTelegram className="text-blue-600 w-4 h-4" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Пост для Telegram</h3>
              <p className="text-sm text-gray-600">Профессиональный анонс для медицинского канала</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPreviewMode(!previewMode)}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <ViewIcon className="mr-2" />
              {previewMode ? 'Редактор' : 'Превью'}
            </button>

            <button
              onClick={handleGenerate}
              disabled={isGenerating || isLoading}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <>
                  <LoadingIcon className="animate-spin mr-2" />
                  Генерируем...
                </>
              ) : (
                <>
                  <ActionIcon className="mr-2" />
                  Сгенерировать пост
                </>
              )}
            </button>
          </div>
        </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Левая панель - Настройки и редактор */}
        <div className="space-y-4">
          {/* Настройки интриги */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-900 mb-3">🎯 Настройки интриги</h4>

            <div className="grid grid-cols-1 gap-4 mb-4">
              <div>
                <label className="block text-xs font-medium text-blue-800 mb-1">Тип зацепки</label>
                <select
                  value={postSettings.hook_type}
                  onChange={(e) => setPostSettings(prev => ({...prev, hook_type: e.target.value}))}
                  className="w-full text-sm border border-blue-300 rounded px-2 py-1 bg-white"
                >
                  <option value="question">❓ Провокационный вопрос</option>
                  <option value="shocking_fact">⚡ Шокирующий факт</option>
                  <option value="statistics">📊 Впечатляющая статистика</option>
                  <option value="contradiction">🔄 Развенчание мифа</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-blue-800 mb-1">Уровень раскрытия</label>
                <select
                  value={postSettings.disclosure_level}
                  onChange={(e) => setPostSettings(prev => ({...prev, disclosure_level: e.target.value}))}
                  className="w-full text-sm border border-blue-300 rounded px-2 py-1 bg-white"
                >
                  <option value="hint">🔍 Только намек (максимальная интрига)</option>
                  <option value="main_idea">💡 Основная идея (средняя интрига)</option>
                  <option value="almost_all">📖 Почти всё (минимальная интрига)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-blue-800 mb-1">Призыв к действию</label>
                <select
                  value={postSettings.call_to_action}
                  onChange={(e) => setPostSettings(prev => ({...prev, call_to_action: e.target.value}))}
                  className="w-full text-sm border border-blue-300 rounded px-2 py-1 bg-white"
                >
                  <option value="curiosity">🧐 Любопытство ("Подробности →")</option>
                  <option value="urgency">⚡ Срочность ("Читать сейчас →")</option>
                  <option value="expertise">🎓 Экспертность ("Узнать больше →")</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-blue-800 mb-1">Ссылка на статью</label>
              <input
                type="url"
                value={articleUrl}
                onChange={(e) => setArticleUrl(e.target.value)}
                placeholder="https://example.com/статья"
                className="w-full text-sm border border-blue-300 rounded px-2 py-1 bg-white"
              />
              <p className="text-xs text-blue-600 mt-1">Эта ссылка будет использована в кнопке для перехода к статье</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-blue-800 mb-1">Текст кнопки</label>
              <input
                type="text"
                value={linkButtonText}
                onChange={(e) => setLinkButtonText(e.target.value)}
                placeholder="📖 Читать полную статью"
                className="w-full text-sm border border-blue-300 rounded px-2 py-1 bg-white"
              />
              <p className="text-xs text-blue-600 mt-1">Текст кнопки для перехода к статье</p>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={postSettings.include_image}
                  onChange={(e) => setPostSettings(prev => ({...prev, include_image: e.target.checked}))}
                  className="rounded border-blue-300 text-blue-600 mr-2"
                />
                <span className="text-sm text-blue-700">Прикрепить изображение из статьи</span>
              </label>
            </div>
          </div>

          {/* Редактор текста */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Текст поста
            </label>
            <textarea
              id="telegram-post-textarea"
              value={telegramPost}
              onChange={handleTextChange}
              placeholder={
                draftId
                  ? "Нажмите 'Сгенерировать пост' для создания анонса на основе выжимки статьи"
                  : newsId
                  ? "Нажмите 'Сгенерировать пост' для создания анонса опубликованной новости"
                  : "Сначала создайте и подтвердите выжимку статьи"
              }
              className="w-full h-48 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm leading-relaxed"
              disabled={!draftId && !newsId}
            />

            {/* Панель эмодзи */}
            <div className="mt-2">
              <button
                type="button"
                onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                className="flex items-center px-2 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded transition-colors"
              >
                <span className="mr-1">😊</span>
                <span>Добавить эмодзи</span>
              </button>

              {showEmojiPicker && (
                <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="grid grid-cols-8 gap-1">
                    {medicalEmojis.map((emoji, index) => (
                      <button
                        key={index}
                        onClick={() => insertEmoji(emoji)}
                        className="w-8 h-8 w-4 h-4 hover:bg-gray-200 rounded transition-colors flex items-center justify-center"
                        title={`Добавить ${emoji}`}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                  <div className="mt-2 pt-2 border-t border-gray-300">
                    <p className="text-xs text-gray-500">
                      💡 Нажмите на эмодзи, чтобы добавить его в текст поста
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Статистика */}
            <div className="flex items-center justify-between text-sm mt-2">
              <span className={`font-medium ${getCharCountClass()}`}>
                {getCharCount()}/350 символов
              </span>
              <span className="text-gray-500">
                Интрига: 200-350 символов
              </span>
            </div>
          </div>

          {/* Кнопки действий */}
          <div className="flex items-center space-x-3">
            <button
              onClick={handleCopy}
              disabled={!telegramPost.trim()}
              className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {copySuccess ? (
                <>
                  <CheckIconCircle className="mr-2 text-green-600" />
                  Скопировано
                </>
              ) : (
                <>
                  <FaCopy className="mr-2" />
                  Копировать
                </>
              )}
            </button>

            {/* Кнопка сохранения для новой логики */}
            {newsId && (
              <button
                onClick={handleSave}
                disabled={!telegramPost.trim() || isGenerating}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <>
                    <LoadingIcon className="animate-spin mr-2" />
                    Сохраняем...
                  </>
                ) : (
                  <>
                    <FaRocket className="mr-2" />
                    Сохранить пост
                  </>
                )}
              </button>
            )}

            {/* Кнопка публикации в Telegram */}
            {newsId && (
              <button
                onClick={handlePublish}
                disabled={!telegramPost.trim() || isGenerating || isPublishing}
                className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isPublishing ? (
                  <>
                    <LoadingIcon className="animate-spin mr-2" />
                    Публикуем...
                  </>
                ) : (
                  <>
                    <FaTelegram className="mr-2" />
                    Опубликовать в Telegram
                  </>
                )}
              </button>
            )}
          </div>

          {/* Рекомендации по интриге */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-amber-900 mb-2">🎯 Принципы интригующего поста:</h4>
            <ul className="text-sm text-amber-800 space-y-1">
              <li>• <strong>Недосказанность</strong> — не раскрывай всю суть в посте</li>
              <li>• <strong>Крючок</strong> — начни с провокационного элемента</li>
              <li>• <strong>Любопытство</strong> — заставь читателя захотеть узнать больше</li>
              <li>• <strong>Призыв</strong> — обязательно завершай фразой "Подробности →"</li>
              <li>• <strong>Эмодзи</strong> — 1-2 медицинских: 🩺🧬💊🔬📊</li>
              <li>• <strong>Цель</strong> — мотивировать переход на сайт за полной информацией</li>
            </ul>
          </div>
        </div>

        {/* Правая панель - Реалистичный превью */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Превью в Telegram
            </label>

            {/* Точная копия Telegram поста */}
            <div className="bg-green-100 rounded-3xl p-4" style={{background: 'linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%)'}}>
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden max-w-sm mx-auto" style={{maxWidth: '350px'}}>
                {telegramPost ? (
                  <div>
                    {/* Изображение на всю ширину */}
                    {postSettings.include_image && (newsData?.generated_image_url || articleData?.image_url) && (
                      <div className="relative">
                        <img
                          src={newsData?.generated_image_url || articleData?.image_url}
                          alt="Article image"
                          className="w-full h-52 object-cover"
                          style={{borderRadius: '16px 16px 0 0'}}
                          onError={(e) => {
                            const parent = e.target.parentElement;
                            parent.innerHTML = `
                              <div class="w-full h-52 bg-gray-100 flex items-center justify-center" style="border-radius: 16px 16px 0 0">
                                <div class="text-center text-gray-400">
                                  <svg class="mx-auto h-10 w-10 mb-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
                                  </svg>
                                  <div class="text-sm">Изображение недоступно</div>
                                </div>
                              </div>
                            `;
                          }}
                        />
                      </div>
                    )}

                    {/* Контент поста */}
                    <div className="p-4">
                      <div className="text-base text-black leading-relaxed font-normal">
                        {parseFormattedText(telegramPost)}

                        {/* Показываем ссылку как будет в итоговом посте */}
                        {articleUrl && (
                          <>
                            <div className="h-4">&nbsp;</div>
                            <div className="text-blue-500 underline cursor-pointer">
                              {linkButtonText}
                            </div>
                          </>
                        )}
                      </div>

                    </div>

                    {/* Реакции и статистика */}
                    <div className="px-4 pb-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div className="flex items-center space-x-1 px-2 py-1 bg-red-50 rounded-full">
                            <span style={{fontSize: '14px'}}>❤️</span>
                            <span className="text-gray-700 font-medium text-sm">8</span>
                          </div>
                          <div className="flex items-center space-x-1 px-2 py-1 bg-blue-50 rounded-full">
                            <span style={{fontSize: '14px'}}>👍</span>
                            <span className="text-gray-700 font-medium text-sm">8</span>
                          </div>
                          <div className="flex items-center space-x-1 px-2 py-1 bg-orange-50 rounded-full">
                            <span style={{fontSize: '14px'}}>🔥</span>
                            <span className="text-gray-700 font-medium text-sm">5</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <span className="flex items-center">
                            <HiEye className="w-4 h-4 mr-1" />
                            <span>1K</span>
                          </span>
                          <span>{new Date().toLocaleTimeString('ru', {hour: '2-digit', minute: '2-digit'})}</span>
                        </div>
                      </div>
                    </div>

                    {/* Кнопка комментировать */}
                    <div className="border-t border-gray-100">
                      <button className="w-full px-4 py-3 text-left flex items-center justify-between text-blue-600 hover:bg-gray-50 transition-colors">
                        <div className="flex items-center space-x-3">
                          <FaComments className="w-4 h-4" />
                          <span className="font-medium">Прокомментировать</span>
                        </div>
                        <span className="text-gray-400">→</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center">
                    <div className="mb-3">
                      <FaTelegram className="mx-auto w-8 h-8 text-gray-300" />
                    </div>
                    <div className="text-gray-500">
                      <div className="text-sm mb-1">Настройте параметры и нажмите</div>
                      <div className="text-sm font-medium">"Сгенерировать пост"</div>
                      <div className="text-xs mt-2 opacity-70">
                        Здесь будет отображен точный превью
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Анализ интриги */}
          {telegramPost && (
            <div className="bg-green-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-900 mb-3">🎯 Анализ интриги</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-green-600">Длина:</span>
                  <span className={`ml-2 font-semibold ${getCharCountClass()}`}>
                    {getCharCount()}/350
                  </span>
                </div>
                <div>
                  <span className="text-green-600">Эмодзи:</span>
                  <span className="ml-2 font-semibold text-green-900">
                    {(telegramPost.match(/[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu) || []).length}
                  </span>
                </div>
                <div>
                  <span className="text-green-600">Призыв:</span>
                  <span className="ml-2 font-semibold text-green-900">
                    {telegramPost.includes('→') ? '✓' : '✗'}
                  </span>
                </div>
                <div>
                  <span className="text-green-600">Интрига:</span>
                  <span className="ml-2 font-semibold text-green-900">
                    {postSettings.disclosure_level === 'hint' ? 'Высокая' :
                     postSettings.disclosure_level === 'main_idea' ? 'Средняя' : 'Низкая'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    );
  }

  return <TelegramPostEditorContent />;
};

export default TelegramPostEditor;