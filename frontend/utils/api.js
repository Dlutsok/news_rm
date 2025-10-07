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
        // Логируем детали ошибки для отладки
        console.error('API Error Response:', {
          status: response.status,
          statusText: response.statusText,
          endpoint: endpoint,
          data: data
        })

        // Формируем понятное сообщение об ошибке
        const errorMessage = data?.detail || data?.message || `HTTP ${response.status}: ${response.statusText}`
        throw new Error(errorMessage);
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
    // Используем Next.js API роут для установки HttpOnly cookie
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
      credentials: 'include', // Важно для работы с cookies
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || 'Login failed');
    }

    const data = await response.json();
    
    // Токен теперь в HttpOnly cookie, не сохраняем в localStorage
    return data;
  }

  async getCurrentUser() {
    // Используем прямой API роут для получения текущего пользователя
    const response = await fetch('/api/auth/me', {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized');
      }
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || 'Failed to get current user');
    }

    return await response.json();
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

  /**
   * Получить список платформ
   */
  async getPlatforms() {
    return await this.request('/api/admin/platforms');
  }

  /**
   * Распарсить статью из URL
   */
  async parseURLArticle(url) {
    return await this.request('/api/url-articles/parse', {
      method: 'POST',
      body: JSON.stringify({
        url: url,
        project: 'therapy.school' // ProjectType.THERAPY enum value
      })
    });
  }

  /**
   * Сгенерировать статью из URL (полный цикл: парсинг + генерация + изображение)
   * @param {string} url - URL статьи
   * @param {string} project - Название проекта (gynecology.school, therapy.school, pediatrics.school)
   * @param {boolean} generateImage - Генерировать ли изображение (по умолчанию true)
   * @param {object} formattingOptions - Опции форматирования статьи (опционально)
   * @returns {Promise} - Результат генерации с draft_id и данными статьи
   */
  async generateFromURL(url, project, generateImage = true, formattingOptions = null) {
    const payload = {
      url: url,
      project: project,
      generate_image: generateImage
    }

    // Добавляем formatting_options только если они заданы
    if (formattingOptions) {
      payload.formatting_options = formattingOptions
    }

    return await this.request('/api/url-articles/generate-from-url', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
}

// Создаем единственный экземпляр API клиента
const apiClient = new ApiClient();

export default apiClient;