# Authentication Flow - JWT + Bearer Tokens

## Обзор

Система Medical News Automation использует JWT (JSON Web Tokens) для аутентификации пользователей. Токены передаются через HTTP заголовок `Authorization` с типом `Bearer`.

## Текущая реализация

### Технологии
- **JWT (JSON Web Tokens)** - для создания и верификации токенов
- **bcrypt** - для хеширования паролей
- **FastAPI dependencies** - для проверки авторизации на endpoint уровне
- **Bearer Token** - токен передается в заголовке `Authorization: Bearer <token>`

### Схема аутентификации

```
┌─────────────┐                   ┌─────────────┐                   ┌─────────────┐
│             │                   │             │                   │             │
│   Frontend  │                   │   Backend   │                   │  Database   │
│   (Next.js) │                   │  (FastAPI)  │                   │  (SQLite)   │
│             │                   │             │                   │             │
└──────┬──────┘                   └──────┬──────┘                   └──────┬──────┘
       │                                 │                                 │
       │  1. POST /api/auth/login        │                                 │
       │  { username, password }         │                                 │
       ├────────────────────────────────>│                                 │
       │                                 │                                 │
       │                                 │  2. Запрос пользователя         │
       │                                 ├────────────────────────────────>│
       │                                 │                                 │
       │                                 │  3. User данные                 │
       │                                 │<────────────────────────────────┤
       │                                 │                                 │
       │                                 │  4. Проверка пароля (bcrypt)    │
       │                                 │     verify_password()            │
       │                                 │                                 │
       │                                 │  5. Создание JWT токена         │
       │                                 │     create_access_token()        │
       │                                 │     - sub: username              │
       │                                 │     - exp: 12 hours              │
       │                                 │                                 │
       │  6. Response                    │                                 │
       │  { access_token, token_type }   │                                 │
       │<────────────────────────────────┤                                 │
       │                                 │                                 │
       │  7. Сохранение токена           │                                 │
       │     localStorage.setItem()      │                                 │
       │                                 │                                 │
       │  8. Последующие запросы         │                                 │
       │  Headers: Authorization:        │                                 │
       │           Bearer <jwt_token>    │                                 │
       ├────────────────────────────────>│                                 │
       │                                 │                                 │
       │                                 │  9. Верификация токена          │
       │                                 │     decode JWT                   │
       │                                 │     check expiration             │
       │                                 │                                 │
       │                                 │  10. Загрузка пользователя      │
       │                                 ├────────────────────────────────>│
       │                                 │                                 │
       │                                 │  11. User данные                │
       │                                 │<────────────────────────────────┤
       │                                 │                                 │
       │  12. Response с данными         │                                 │
       │<────────────────────────────────┤                                 │
       │                                 │                                 │
```

## Детальное описание flow

### 1. Регистрация/Инициализация

```python
# backend/services/auth_service.py
class AuthService:
    def initialize_admin(self):
        """Создание администратора при первом запуске"""
        # Проверка существования admin пользователя
        # Если нет - создание с дефолтными credentials
        # Пароль хешируется через bcrypt
```

### 2. Процесс логина

**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Backend обработка:**

```python
# 1. Аутентификация пользователя
user = auth_service.authenticate_user(username, password)

# 2. Проверка пароля
def authenticate_user(username: str, password: str) -> User | None:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# 3. Создание JWT токена
access_token = auth_service.create_access_token(
    data={"sub": user.username}
)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=12)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 3. Хранение токена на клиенте

```javascript
// frontend/utils/api.js
// После успешного логина
const response = await api.post('/api/auth/login', {
  username,
  password
});

// Сохранение токена в localStorage
localStorage.setItem('token', response.data.access_token);

// Установка токена в axios headers
api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
```

### 4. Проверка авторизации на защищенных endpoints

**Dependency для проверки:**

```python
# backend/api/dependencies.py

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Получение текущего пользователя из JWT токена"""

    token = credentials.credentials

    try:
        # Декодирование токена
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Загрузка пользователя из БД
    user = auth_service.get_user_by_username(username)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# Dependency для проверки роли
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_staff(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user
```

**Использование на endpoints:**

```python
# backend/api/news_generation.py

@router.post("/generate-summary")
async def generate_summary(
    request: SummaryRequest,
    current_user: User = Depends(require_staff)  # Требуется staff или admin
):
    # Только для staff и admin
    ...

@router.get("/users")
async def get_users(
    current_user: User = Depends(require_admin)  # Требуется только admin
):
    # Только для admin
    ...
```

### 5. Проверка токена

**Endpoint:** `POST /api/auth/verify-token`

```python
@router.post("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Проверка валидности токена"""
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "project": current_user.project
        }
    }
```

### 6. Получение информации о текущем пользователе

**Endpoint:** `GET /api/auth/me`

```python
@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        project=current_user.project,
        created_at=current_user.created_at
    )
```

## Ролевая модель

### Роли пользователей

```python
class UserRole(str, Enum):
    ADMIN = "admin"    # Полный доступ
    STAFF = "staff"    # Создание и управление контентом
    ANALYST = "analyst" # Только просмотр
```

### Матрица доступа

| Endpoint | Public | Analyst | Staff | Admin |
|----------|--------|---------|-------|-------|
| POST /api/auth/login | ✓ | ✓ | ✓ | ✓ |
| GET /api/auth/me | ✗ | ✓ | ✓ | ✓ |
| GET /api/news/articles | ✗ | ✓ | ✓ | ✓ |
| POST /api/news/parse | ✗ | ✗ | ✓ | ✓ |
| POST /api/news-generation/* | ✗ | ✗ | ✓ | ✓ |
| GET /api/expenses | ✗ | ✓ | ✓ | ✓ |
| POST /api/users | ✗ | ✗ | ✗ | ✓ |
| PUT /api/users/{id} | ✗ | ✗ | ✗ | ✓ |
| GET /api/admin/* | ✗ | ✗ | ✗ | ✓ |

## Настройки безопасности

### JWT конфигурация

```python
# backend/core/config.py
class Settings:
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 12
```

### Переменные окружения

```bash
# .env файл (production)
JWT_SECRET_KEY="ваш-секретный-ключ-256-бит-минимум"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="надежный-пароль"
```

### Хеширование паролей

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

## Frontend интеграция

### AuthContext

```javascript
// frontend/contexts/AuthContext.js
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Проверка токена при загрузке
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      checkAuth();
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuth = async () => {
    try {
      const response = await api.get('/api/auth/me');
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const response = await api.post('/api/auth/login', {
      username,
      password
    });
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    await checkAuth();
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Protected Routes

```javascript
// frontend/components/ProtectedRoute.js
function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return null;
  }

  // Проверка роли если указана
  if (requiredRole && user.role !== requiredRole && user.role !== 'admin') {
    return <div>Access denied</div>;
  }

  return children;
}
```

## Важные замечания

### Текущее состояние (октябрь 2025)

1. **JWT токены** - основной метод аутентификации
2. **Bearer Token** - токен передается в заголовке Authorization
3. **localStorage** - токен хранится на клиенте в localStorage
4. **Срок действия** - 12 часов (ACCESS_TOKEN_EXPIRE_HOURS=12)
5. **Без refresh tokens** - после истечения требуется повторный логин

### Известные ограничения

1. **Нет HttpOnly cookies** - токен доступен через JavaScript (XSS риск)
2. **Нет refresh token механизма** - пользователь должен логиниться каждые 12 часов
3. **Нет token revocation** - нет blacklist для отозванных токенов
4. **Нет rate limiting на /login** - можно улучшить защиту от brute force

### Рекомендации по улучшению

1. **Добавить HttpOnly cookies** для хранения токенов
2. **Реализовать refresh token механизм**
3. **Добавить token blacklist** для logout и revocation
4. **Усилить rate limiting** на authentication endpoints
5. **Добавить 2FA** для критических операций
6. **Логирование всех authentication events**

## Troubleshooting

### Типичные ошибки

**401 Unauthorized - Invalid token**
- Токен истек (> 12 часов)
- Токен поврежден
- Неверный JWT_SECRET_KEY

**403 Forbidden - Access denied**
- Недостаточно прав для операции
- Проверьте роль пользователя

**Token not provided**
- Заголовок Authorization отсутствует
- Неправильный формат: должно быть `Bearer <token>`

### Отладка

```python
# backend/api/dependencies.py
import logging
logger = logging.getLogger(__name__)

# Добавить логирование в get_current_user
logger.info(f"Token verification for user: {username}")
logger.error(f"JWT decode error: {str(e)}")
```

## См. также

- [API Endpoints Documentation](../api/endpoints.md)
- [Security Overview](./overview.md)
- [User Management](../api/endpoints.md#пользователи)
