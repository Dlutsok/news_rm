import { useState, useEffect } from 'react';
import {
  UserIcon,
  PlusIcon,
  DeleteIcon,
  LoadingIcon,
  CheckIcon,
  XIcon,
  KeyIcon,
  CrownIcon
} from './ui/icons';
import apiClient from '@utils/api';

const UserManager = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    role: 'staff',
    project: ''
  });
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [passwordModal, setPasswordModal] = useState({ open: false, userId: null, username: '', newPassword: '' });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getUsers();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
      setMessage({ type: 'error', text: 'Ошибка загрузки пользователей' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    if (!newUser.username.trim() || !newUser.password.trim()) {
      setMessage({ type: 'error', text: 'Заполните все поля' });
      return;
    }

    setIsCreating(true);
    setMessage({ type: '', text: '' });

    try {
      await apiClient.createUser(newUser);
      
      setMessage({ type: 'success', text: 'Пользователь успешно создан' });
      setNewUser({ username: '', password: '', role: 'staff', project: '' });
      setShowCreateForm(false);
      
      // Обновляем список пользователей
      await fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      setMessage({ 
        type: 'error', 
        text: error.message || 'Ошибка создания пользователя' 
      });
    } finally {
      setIsCreating(false);
    }
  };

  const getRoleText = (role) => {
    switch (role) {
      case 'admin':
        return 'Администратор';
      case 'staff':
        return 'Сотрудник';
      case 'analyst':
        return 'Аналитик';
      default:
        return role;
    }
  };

  const getProjectText = (project) => {
    switch (project) {
      case 'GYNECOLOGY':
        return 'Gynecology School';
      case 'THERAPY':
        return 'Therapy School';
      case 'PEDIATRICS':
        return 'Pediatrics School';
      default:
        return project;
    }
  };

  const handleDelete = async (userId) => {
    if (!confirm('Удалить пользователя?')) return;
    try {
      await apiClient.deleteUser(userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Ошибка удаления пользователя' });
    }
  };

  const openChangePassword = (user) => {
    setPasswordModal({ open: true, userId: user.id, username: user.username, newPassword: '' });
  };

  const submitChangePassword = async () => {
    if (!passwordModal.newPassword || passwordModal.newPassword.length < 6) {
      setMessage({ type: 'error', text: 'Минимальная длина пароля 6 символов' });
      return;
    }
    try {
      await apiClient.updateUserPassword(passwordModal.userId, passwordModal.newPassword);
      setMessage({ type: 'success', text: 'Пароль обновлен' });
      setPasswordModal({ open: false, userId: null, username: '', newPassword: '' });
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Ошибка смены пароля' });
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-yellow-100 text-yellow-800';
      case 'staff':
        return 'bg-blue-100 text-blue-800';
      case 'analyst':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingIcon className="animate-spin text-gray-400 w-6 h-6 mr-2" />
        <span className="text-gray-600">Загрузка пользователей...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Управление пользователями</h2>
          <p className="text-gray-600 mt-1">Создание и управление учетными записями сотрудников</p>
        </div>
        
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center transition-colors"
        >
          <PlusIcon className="mr-2" />
          Создать пользователя
        </button>
      </div>

      {/* Messages */}
      {message.text && (
        <div className={`p-4 rounded-lg ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-700 border border-green-200' 
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          <div className="flex items-center">
            {message.type === 'success' ? (
              <CheckIcon className="mr-2" />
            ) : (
              <XIcon className="mr-2" />
            )}
            {message.text}
          </div>
        </div>
      )}

      {/* Create User Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Создать нового пользователя</h3>
          
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Имя пользователя
                </label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Введите имя пользователя"
                  disabled={isCreating}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Пароль
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Введите пароль"
                  disabled={isCreating}
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Роль
                </label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isCreating}
                >
                  <option value="staff">Сотрудник</option>
                  <option value="admin">Администратор</option>
                  <option value="analyst">Аналитик</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Проект
                </label>
                <select
                  value={newUser.project}
                  onChange={(e) => setNewUser({ ...newUser, project: e.target.value || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isCreating}
                >
                  <option value="">Не назначен</option>
                  <option value="GYNECOLOGY">Gynecology School</option>
                  <option value="THERAPY">Therapy School</option>
                  <option value="PEDIATRICS">Pediatrics School</option>
                </select>
              </div>
            </div>
            
            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setNewUser({ username: '', password: '', role: 'staff', project: '' });
                  setMessage({ type: '', text: '' });
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                disabled={isCreating}
              >
                Отмена
              </button>
              
              <button
                type="submit"
                disabled={isCreating || !newUser.username.trim() || !newUser.password.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? (
                  <>
                    <LoadingIcon className="animate-spin mr-2" />
                    Создание...
                  </>
                ) : (
                  <>
                    <PlusIcon className="mr-2" />
                    Создать
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Users List */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Список пользователей ({users.length})
          </h3>
        </div>
        
        {users.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <UserIcon className="mx-auto w-10 h-10 text-gray-300 mb-4" />
            <p>Пользователи не найдены</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Пользователь
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Роль
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Проект
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Создан
                  </th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full mr-3">
                          {user.role === 'admin' ? (
                            <CrownIcon className="text-yellow-600" />
                          ) : (
                            <UserIcon className="text-gray-600" />
                          )}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {user.username}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {user.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                        {getRoleText(user.role)}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.project ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {getProjectText(user.project)}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">Не назначен</span>
                      )}
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex items-center justify-end space-x-3">
                        <button
                          onClick={() => openChangePassword(user)}
                          className="inline-flex items-center px-3 py-1.5 border border-gray-200 rounded-md text-gray-700 hover:bg-gray-50"
                        >
                          <KeyIcon className="mr-2" /> Пароль
                        </button>
                        <button
                          onClick={() => handleDelete(user.id)}
                          className="inline-flex items-center px-3 py-1.5 border border-red-200 rounded-md text-red-600 hover:bg-red-50"
                        >
                          <DeleteIcon className="mr-2" /> Удалить
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Change Password */}
      {passwordModal.open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Смена пароля</h3>
            <p className="text-sm text-gray-600 mb-4">Пользователь: <span className="font-medium">{passwordModal.username}</span></p>
            <div className="space-y-2 mb-6">
              <label className="block text-sm font-medium text-gray-700">Новый пароль</label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={passwordModal.newPassword}
                onChange={(e) => setPasswordModal((m) => ({ ...m, newPassword: e.target.value }))}
                placeholder="Минимум 6 символов"
              />
            </div>
            <div className="flex items-center justify-end space-x-3">
              <button
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
                onClick={() => setPasswordModal({ open: false, userId: null, username: '', newPassword: '' })}
              >
                Отмена
              </button>
              <button
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
                onClick={submitChangePassword}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManager;