/**
 * API клиент для работы с backend через Next.js API routes
 * Все запросы идут через Next.js API routes для корректной работы с HttpOnly cookies
 */

class ApiClient {
  // Токены хранятся в HttpOnly cookies, baseURL и localStorage не нужны

  /**
   * Универсальный метод для HTTP запросов
   * Production: Auth/Users/Settings → Next.js API routes, остальное → /api/proxy
   * Development (localhost): ВСЕ /api/* → /api/proxy (backend не доступен напрямую)
   */
  async request(endpoint, options = {}) {
    // На localhost всегда используем proxy для всех /api/* запросов
    const isLocalhost = typeof window !== 'undefined' &&
                       (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

    let finalEndpoint = endpoint;

    if (endpoint.startsWith('/api/') && !endpoint.startsWith('/api/proxy')) {
      if (isLocalhost) {
        // На localhost ВСЕ идет через proxy
        finalEndpoint = `/api/proxy${endpoint}`;
      } else {
        // На production: только не-auth/users/settings идут через proxy
        const needsProxy = !endpoint.startsWith('/api/auth') &&
                          !endpoint.startsWith('/api/users') &&
                          !endpoint.startsWith('/api/settings');
        if (needsProxy) {
          finalEndpoint = `/api/proxy${endpoint}`;
        }
      }
    }

    // Читаем CSRF token из cookie для POST/PUT/DELETE/PATCH
    const needsCsrf = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method);
    let csrfToken = null;

    if (needsCsrf && typeof document !== 'undefined') {
      csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];
    }

    const config = {
      credentials: 'include', // Важно для передачи cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
        // Добавляем CSRF token если он есть и метод требует защиты
        ...(csrfToken && needsCsrf ? { 'X-CSRF-Token': decodeURIComponent(csrfToken) } : {}),
      },
      ...options,
    };

    console.log('🟡 [apiClient] Отправляем запрос:', options.method || 'GET', finalEndpoint);

    try {
      const response = await fetch(finalEndpoint, config);
      console.log('🟡 [apiClient] Получен ответ:', response.status, response.statusText);

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
    return await this.request('/api/users');
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
    return await this.request('/api/news');
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