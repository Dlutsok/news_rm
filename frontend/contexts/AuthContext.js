import { createContext, useContext, useReducer, useEffect } from 'react';
import apiClient from '@utils/api';

// Начальное состояние
const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Типы действий
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_ERROR: 'LOGIN_ERROR',
  LOGOUT: 'LOGOUT',
  LOAD_USER_START: 'LOAD_USER_START',
  LOAD_USER_SUCCESS: 'LOAD_USER_SUCCESS',
  LOAD_USER_ERROR: 'LOAD_USER_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer для управления состоянием авторизации
function authReducer(state, action) {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
    case AUTH_ACTIONS.LOAD_USER_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_SUCCESS:
    case AUTH_ACTIONS.LOAD_USER_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_ERROR:
    case AUTH_ACTIONS.LOAD_USER_ERROR:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload.error,
      };

    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };

    default:
      return state;
  }
}

// Создаем контекст
const AuthContext = createContext();

// Hook для использования контекста авторизации
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Provider компонент
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);


  // Загружаем пользователя при инициализации
  useEffect(() => {
    loadUser();
  }, []);


  // Загрузить текущего пользователя
  const loadUser = async () => {
    // При использовании HttpOnly cookie не проверяем наличие токена в JS

    try {
      dispatch({ type: AUTH_ACTIONS.LOAD_USER_START });

      const user = await apiClient.getCurrentUser();

      dispatch({
        type: AUTH_ACTIONS.LOAD_USER_SUCCESS,
        payload: { user },
      });
    } catch (error) {
      // Не логируем ошибку авторизации, это нормально для неавторизованных пользователей
      if (error.message !== 'Unauthorized') {
        console.error('Failed to load user:', error);
      }

      dispatch({
        type: AUTH_ACTIONS.LOAD_USER_ERROR,
        payload: { error: error.message },
      });
    }
  };

  // Вход в систему
  const login = async (username, password) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });

      const response = await apiClient.login(username, password);
      
      // Получаем данные пользователя после успешного входа
      const user = await apiClient.getCurrentUser();


      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: { user },
      });

      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      
      dispatch({
        type: AUTH_ACTIONS.LOGIN_ERROR,
        payload: { error: error.message },
      });

      return { success: false, error: error.message };
    }
  };

  // Выход из системы
  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    } catch {}

    dispatch({ type: AUTH_ACTIONS.LOGOUT });
  };

  // Очистить ошибку
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  // Проверить является ли пользователь администратором
  const isAdmin = () => {
    return state.user?.role === 'admin';
  };

  // Проверить является ли пользователь сотрудником (включая админа)
  const isStaff = () => {
    return state.user?.role === 'admin' || state.user?.role === 'staff' || state.user?.role === 'analyst';
  };

  // Проверить является ли пользователь аналитиком
  const isAnalyst = () => state.user?.role === 'analyst';

  const value = {
    ...state,
    login,
    logout,
    loadUser,
    clearError,
    isAdmin,
    isStaff,
    isAnalyst,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;