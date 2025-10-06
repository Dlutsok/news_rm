/**
 * API клиент для работы с backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  /**
   * Получить токен из localStorage
   */
  getToken() {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  /**
   * Сохранить токен в localStorage
   */
  setToken(token) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  /**
   * Удалить токен из localStorage
   */
  removeToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  /**
   * Универсальный метод для HTTP запросов
   */
  async request(endpoint, options = {}) {
    // Все API запросы идут напрямую на backend через nginx
    const url = endpoint.startsWith('/api/') ? `${this.baseURL}${endpoint}` : `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Добавляем Authorization header если токен есть
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      
      // Если токен не валиден, перенаправляем на логин, но избегаем петли на /login
      if (response.status === 401) {
        // Не перенаправляем автоматически для запросов getCurrentUser при первой загрузке
        if (typeof window !== 'undefined' && endpoint !== '/api/auth/me') {
          const path = window.location?.pathname || ''
          if (path !== '/login') {
            window.location.href = '/login';
          }
        }
        throw new Error('Unauthorized');
      }

      // Парсим JSON если есть контент
      let data = null;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      }

      if (!response.ok) {
        throw new Error(data?.detail || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      // Не логируем ошибки авторизации для /api/auth/me, это нормально
      if (!(error.message === 'Unauthorized' && endpoint === '/api/auth/me')) {
        console.error('API request failed:', error);
      }
      throw error;
    }
  }

  // Auth endpoints
  async login(username, password) {
    // Используем универсальный метод request для единообразия
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    // Сохраняем токен в localStorage
    if (data.access_token) {
      this.setToken(data.access_token);
    }

    return data;
  }

  async getCurrentUser() {
    return await this.request('/api/auth/me');
  }

  async verifyToken() {
    return await this.request('/api/auth/verify-token', { method: 'POST' });
  }

  // Users endpoints
  async getUsers() {
    return await this.request('/api/users/');
  }

  async createUser(userData) {
    return await this.request('/api/users/create', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId) {
    return await this.request(`/api/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async updateUserPassword(userId, newPassword) {
    return await this.request(`/api/users/${userId}/password`, {
      method: 'POST',
      body: JSON.stringify({ password: newPassword }),
    });
  }

  // Settings endpoints (требуют авторизации)
  async getSettings() {
    return await this.request('/api/settings/all');
  }

  async getBitrixProjects() {
    return await this.request('/api/settings/bitrix-projects');
  }

  async createBitrixProject(projectData) {
    return await this.request('/api/settings/bitrix-projects', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  }

  async updateBitrixProject(projectCode, projectData) {
    return await this.request(`/api/settings/bitrix-projects/${projectCode}`, {
      method: 'PUT',
      body: JSON.stringify(projectData),
    });
  }

  async deleteBitrixProject(projectCode) {
    return await this.request(`/api/settings/bitrix-projects/${projectCode}`, {
      method: 'DELETE',
    });
  }

  // System settings endpoints
  async getSystemSettings() {
    return await this.request('/api/settings/system');
  }

  async updateSystemSettings(settingsData) {
    return await this.request('/api/settings/system', {
      method: 'PUT',
      body: JSON.stringify(settingsData),
    });
  }

  // News endpoints
  async getNews() {
    return await this.request('/api/news/');
  }

  async parseNews(sources, articleCount) {
    return await this.request('/api/news/parse', {
      method: 'POST',
      body: JSON.stringify({ sources, article_count: articleCount }),
    });
  }

  // Health check
  async healthCheck() {
    return await this.request('/api/health');
  }
}

// Создаем единственный экземпляр API клиента
const apiClient = new ApiClient();

export default apiClient;