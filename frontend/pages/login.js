import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import {
  LoadingIcon,
  ViewIcon,
  HideIcon,
  RobotIcon
} from '../components/ui/icons';
import { useAuth } from '@contexts/AuthContext';

export default function Login() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { login, isAuthenticated, isLoading, error, clearError } = useAuth();
  const router = useRouter();

  // Если уже авторизован, перенаправляем на главную
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  // Очищаем ошибки при изменении полей
  useEffect(() => {
    if (error) {
      clearError();
    }
  }, [formData.username, formData.password]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.username.trim() || !formData.password.trim()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await login(formData.username, formData.password);
      
      if (result.success) {
        // Даем время для сохранения токена и обновления состояния
        setTimeout(() => {
          router.push('/');
        }, 100);
      }
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Показываем загрузку пока проверяем авторизацию
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-500 text-sm">Проверка авторизации...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Вход в систему - Rusmedical News AI</title>
        <meta name="description" content="Авторизация в системе Rusmedical News AI" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-sky-50">
        <div className="grid grid-cols-1 lg:grid-cols-2 min-h-screen">
          <div className="hidden lg:flex relative items-center justify-center overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 via-violet-600 to-sky-600 opacity-90" />
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-400 rounded-full blur-3xl opacity-40" />
            <div className="absolute -bottom-24 -right-24 w-[28rem] h-[28rem] bg-sky-400 rounded-full blur-3xl opacity-40" />
            <div className="relative z-10 text-white px-12">
              <div className="flex items-center space-x-4 mb-8">
                <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center shadow-lg backdrop-blur-md">
                  <RobotIcon className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h1 className="text-3xl font-semibold">Rusmedical News AI</h1>
                  <p className="text-white/80 text-sm mt-1">Внутренний сервис автоматизации новостей</p>
                </div>
              </div>
              <div className="mt-8 space-y-4 text-white/90">
                <p className="text-lg leading-relaxed max-w-lg">Единый вход для сотрудников. Генерация, редактирование и публикация медицинских новостей в одном месте.</p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center py-12 px-6">
            <div className="w-full max-w-md">
              <div className="text-center mb-8 lg:hidden">
                <div className="mx-auto w-14 h-14 bg-gradient-to-r from-indigo-500 to-sky-500 rounded-2xl flex items-center justify-center mb-4 shadow-lg">
                  <RobotIcon className="w-7 h-7 text-white" />
                </div>
                <h1 className="text-2xl font-semibold text-gray-900">Rusmedical News AI</h1>
                <p className="text-gray-500 text-sm mt-1">Внутренний доступ сотрудников</p>
              </div>

              <div className="bg-white/70 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-100 p-8">
                <form className="space-y-6" onSubmit={handleSubmit}>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">Логин</label>
                      <input
                        id="username"
                        name="username"
                        type="text"
                        autoComplete="username"
                        required
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-100 focus:border-indigo-500 transition-all duration-200 bg-gray-50 focus:bg-white text-gray-900 placeholder-gray-400"
                        placeholder="Введите логин"
                        value={formData.username}
                        onChange={handleInputChange}
                        disabled={isSubmitting}
                      />
                    </div>
                    <div>
                      <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">Пароль</label>
                      <div className="relative">
                        <input
                          id="password"
                          name="password"
                          type={showPassword ? 'text' : 'password'}
                          autoComplete="current-password"
                          required
                          className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-xl focus:outline-none focus:ring-4 focus:ring-indigo-100 focus:border-indigo-500 transition-all duration-200 bg-gray-50 focus:bg-white text-gray-900 placeholder-gray-400"
                          placeholder="Введите пароль"
                          value={formData.password}
                          onChange={handleInputChange}
                          disabled={isSubmitting}
                        />
                        <button
                          type="button"
                          className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none transition-colors duration-200"
                          onClick={() => setShowPassword(!showPassword)}
                          disabled={isSubmitting}
                          aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                        >
                          {showPassword ? <HideIcon className="w-5 h-5" /> : <ViewIcon className="w-5 h-5" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {error && error !== 'Unauthorized' && (
                    <div className="rounded-xl bg-red-50 border border-red-100 p-4">
                      <div className="flex items-center">
                        <svg className="w-5 h-5 text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <span className="text-sm text-red-700">{error === 'Incorrect username or password' ? 'Неверное имя пользователя или пароль' : error}</span>
                      </div>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={isSubmitting || !formData.username.trim() || !formData.password.trim()}
                    className={`w-full py-3 px-4 rounded-xl font-medium text-white transition-all duration-200 transform ${
                      isSubmitting || !formData.username.trim() || !formData.password.trim()
                        ? 'bg-gray-300 cursor-not-allowed'
                        : 'bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-700 hover:to-sky-700 hover:scale-[1.01] active:scale-[0.99] shadow-lg hover:shadow-xl'
                    }`}
                  >
                    {isSubmitting ? (
                      <div className="flex items-center justify-center">
                        <LoadingIcon className="animate-spin w-5 h-5 mr-2" />
                        Выполняется вход...
                      </div>
                    ) : (
                      'Войти'
                    )}
                  </button>
                </form>
              </div>

              {/* Удалено: блок с данными для входа по умолчанию */}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}