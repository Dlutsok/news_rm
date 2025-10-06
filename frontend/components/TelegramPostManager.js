import React, { useState, useEffect } from 'react';
import { FaTelegram, FaCopy } from 'react-icons/fa';
import {
  XIcon,
  PlusIcon,
  LoadingIcon,
  DeleteIcon,
  EditIcon
} from './ui/icons';
import TelegramPostEditor from './TelegramPostEditor';

const TelegramPostManager = ({ newsId, isOpen, onClose, newsData }) => {
  const [existingPosts, setExistingPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditor, setShowEditor] = useState(false);
  const [editingPost, setEditingPost] = useState(null);

  // Загружаем существующие посты при открытии
  useEffect(() => {
    if (isOpen && newsId) {
      fetchExistingPosts();
    }
  }, [isOpen, newsId]);

  const fetchExistingPosts = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await fetch(`/api/telegram-posts/news/${newsId}`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Ошибка при загрузке Telegram постов');
      }

      const posts = await response.json();
      setExistingPosts(posts);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePost = () => {
    setEditingPost(null);
    setShowEditor(true);
  };

  const handleEditPost = (post) => {
    setEditingPost(post);
    setShowEditor(true);
  };

  const handleDeletePost = async (postId) => {
    if (!confirm('Удалить этот Telegram пост?')) return;

    try {
      const response = await fetch(`/api/telegram-posts/${postId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Ошибка при удалении поста');
      }

      // Обновляем список постов
      setExistingPosts(posts => posts.filter(p => p.id !== postId));
    } catch (err) {
      alert(`Ошибка: ${err.message}`);
    }
  };

  const handleCopyPost = (postText) => {
    navigator.clipboard.writeText(postText);
    alert('Пост скопирован в буфер обмена!');
  };

  const handlePostSaved = () => {
    // Закрываем редактор и обновляем список
    setShowEditor(false);
    setEditingPost(null);
    fetchExistingPosts();
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getHookTypeLabel = (hookType) => {
    const labels = {
      'question': '❓ Вопрос',
      'shocking_fact': '⚡ Шокирующий факт',
      'statistics': '📊 Статистика',
      'contradiction': '⚔️ Противоречие'
    };
    return labels[hookType] || hookType;
  };

  const getDisclosureLevelLabel = (level) => {
    const labels = {
      'hint': '🔍 Намек',
      'main_idea': '💡 Основная идея',
      'almost_all': '📝 Почти все'
    };
    return labels[level] || level;
  };

  if (!isOpen) return null;

  // Если показываем редактор
  if (showEditor) {
    return (
      <TelegramPostEditor
        isOpen={true}
        onClose={() => {
          setShowEditor(false);
          setEditingPost(null);
        }}
        newsId={newsId}
        newsData={newsData}
        existingPost={editingPost}
        onPostSaved={handlePostSaved}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
      <div className="bg-white rounded-lg shadow-xl w-full mx-4 max-w-6xl max-h-[95vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FaTelegram className="text-blue-500 w-5 h-5" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Telegram посты</h2>
              <p className="text-sm text-gray-600">
                {newsData?.title ? `${newsData.title.substring(0, 60)}...` : 'Управление постами'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCreatePost}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <PlusIcon  />
              Создать пост
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors p-2 rounded-lg hover:bg-gray-100"
              title="Закрыть"
            >
              <XIcon  />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <LoadingIcon className="animate-spin text-blue-600 w-6 h-6 mx-auto mb-4" />
              <p className="text-gray-600">Загрузка постов...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={fetchExistingPosts}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                Попробовать снова
              </button>
            </div>
          ) : existingPosts.length === 0 ? (
            <div className="text-center py-12">
              <FaTelegram className="text-gray-300 w-10 h-10 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">Пока нет созданных Telegram постов</p>
              <button
                onClick={handleCreatePost}
                className="flex items-center gap-2 mx-auto px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <PlusIcon  />
                Создать первый пост
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between mb-6">
                <p className="text-gray-600">
                  Найдено постов: <span className="font-medium">{existingPosts.length}</span>
                </p>
              </div>

              {/* Список постов */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {existingPosts.map((post) => (
                  <div key={post.id} className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                    {/* Заголовок поста */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-gray-600">
                            #{post.id}
                          </span>
                          <span className="text-xs text-gray-500">
                            {formatDateTime(post.created_at)}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1 mb-3">
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                            {getHookTypeLabel(post.hook_type)}
                          </span>
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                            {getDisclosureLevelLabel(post.disclosure_level)}
                          </span>
                          <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                            {post.character_count} символов
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Превью поста */}
                    <div className="bg-white rounded-lg p-4 mb-4 border border-gray-200">
                      <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {post.post_text}
                      </div>
                    </div>

                    {/* Действия */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleCopyPost(post.post_text)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                      >
                        <FaCopy  />
                        Копировать
                      </button>
                      <button
                        onClick={() => handleEditPost(post)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-purple-600 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
                      >
                        <EditIcon  />
                        Редактировать
                      </button>
                      <button
                        onClick={() => handleDeletePost(post.id)}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                      >
                        <DeleteIcon  />
                        Удалить
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TelegramPostManager;