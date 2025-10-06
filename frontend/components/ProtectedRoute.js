import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@contexts/AuthContext';

/**
 * HOC для защищенных страниц
 */
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, isLoading, user, isAdmin, isStaff } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        // Если не авторизован, перенаправляем на логин
        router.push('/login');
        return;
      }

      if (requireAdmin && !isAdmin()) {
        // Если требуется админ, но пользователь не админ
        console.warn('Access denied: Admin role required');
        router.push('/'); // Перенаправляем на главную
        return;
      }
    }
  }, [isAuthenticated, isLoading, user, requireAdmin, router]);

  // Показываем загрузку пока проверяем авторизацию
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Проверка авторизации...</p>
        </div>
      </div>
    );
  }

  // Если не авторизован или не хватает прав, не показываем контент
  if (!isAuthenticated || (requireAdmin && !isAdmin())) {
    return null;
  }

  return children;
};

export default ProtectedRoute;