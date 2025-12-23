"""
OpenAI провайдер с поддержкой прокси для обхода блокировок
"""

import os
import httpx
import logging
from typing import Dict, List, Optional, Any, AsyncIterator
from core.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI провайдер с поддержкой прокси"""
    
    def __init__(self, api_key: str, proxy_url: str = None):
        self.api_key = api_key
        self.proxy_url = proxy_url
        self.base_url = "https://api.openai.com/v1"
        
        # Безопасное логирование прокси (маскируем пароль)
        if self.proxy_url:
            masked_proxy = self._mask_proxy_password(self.proxy_url)
            logger.info(f"🔗 OpenAI настроен с прокси: {masked_proxy}")
        else:
            logger.info("🔗 OpenAI настроен без прокси")
    
    def _mask_proxy_password(self, proxy_url: str) -> str:
        """Маскирует пароль в URL прокси для логов"""
        if '@' in proxy_url:
            parts = proxy_url.split('@')
            if ':' in parts[0]:
                auth_part = parts[0].split(':')
                auth_part[-1] = '***'  # Заменяем пароль
                parts[0] = ':'.join(auth_part)
            return '@'.join(parts)
        return proxy_url
    
    async def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o-mini", 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Получение ответа от OpenAI API
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            model: Модель OpenAI
            **kwargs: Дополнительные параметры (temperature, max_tokens, etc.)
            
        Returns:
            Dict с ответом от API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 1000),
            "top_p": kwargs.get('top_p', 1.0),
            "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
            "presence_penalty": kwargs.get('presence_penalty', 0.0),
        }
        
        # Удаляем None значения
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Настройка клиента с прокси
        client_kwargs = {"timeout": httpx.Timeout(60.0)}
        if self.proxy_url:
            client_kwargs['proxy'] = self.proxy_url
            logger.debug(f"🔗 Используется прокси для OpenAI запроса к модели {model}")

        async with httpx.AsyncClient(**client_kwargs) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model)
                }
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} при запросе к OpenAI: {e.response.text}")
                raise Exception(f"OpenAI API error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Request error при запросе к OpenAI: {str(e)}")
                raise Exception(f"Ошибка соединения с OpenAI: {str(e)}")
    
    async def get_streaming_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o-mini", 
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Получение стримингового ответа от OpenAI API
        
        Args:
            messages: Список сообщений
            model: Модель OpenAI
            **kwargs: Дополнительные параметры
            
        Yields:
            Dict с частями ответа
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 1000),
            "stream": True,
        }
        
        # Настройка клиента с прокси
        client_kwargs = {"timeout": httpx.Timeout(60.0)}
        if self.proxy_url:
            client_kwargs['proxy'] = self.proxy_url
            logger.debug(f"🔗 Используется прокси для стримингового OpenAI запроса к модели {model}")

        async with httpx.AsyncClient(**client_kwargs) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Убираем "data: "
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                if data.get("choices") and data["choices"][0].get("delta"):
                                    delta = data["choices"][0]["delta"]
                                    if "content" in delta:
                                        yield {
                                            "content": delta["content"],
                                            "finish_reason": data["choices"][0].get("finish_reason")
                                        }
                            except json.JSONDecodeError:
                                continue
                                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} при стриминговом запросе к OpenAI: {e.response.text}")
                raise Exception(f"OpenAI streaming API error {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Request error при стриминговом запросе к OpenAI: {str(e)}")
                raise Exception(f"Ошибка соединения с OpenAI при стриминге: {str(e)}")


def create_openai_provider() -> OpenAIProvider:
    """
    Создание экземпляра OpenAI провайдера с настройками из конфигурации
    
    Returns:
        OpenAIProvider: Настроенный провайдер
    """
    api_key = settings.OPENAI_API_KEY
    proxy_url = getattr(settings, 'OPENAI_PROXY_URL', None)
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
    
    return OpenAIProvider(api_key, proxy_url)


# Глобальный экземпляр провайдера
_openai_provider: Optional[OpenAIProvider] = None


def get_openai_provider() -> OpenAIProvider:
    """
    Получение глобального экземпляра OpenAI провайдера
    
    Returns:
        OpenAIProvider: Глобальный провайдер
    """
    global _openai_provider
    if _openai_provider is None:
        _openai_provider = create_openai_provider()
    return _openai_provider


# Синхронная обертка для совместимости с существующим кодом
class OpenAIClient:
    """Обертка для совместимости с существующим кодом"""
    
    def __init__(self, api_key: str):
        self.provider = OpenAIProvider(api_key, getattr(settings, 'OPENAI_PROXY_URL', None))
    
    class ChatCompletion:
        def __init__(self, provider: OpenAIProvider):
            self.provider = provider
        
        class Completions:
            def __init__(self, provider: OpenAIProvider):
                self.provider = provider
            
            async def create(self, **kwargs):
                """Асинхронное создание completion"""
                messages = kwargs.get('messages', [])
                model = kwargs.get('model', 'gpt-4o-mini')
                
                # Убираем параметры, которые не нужны для нашего API
                clean_kwargs = {k: v for k, v in kwargs.items() 
                               if k not in ['messages', 'model', 'stream']}
                
                if kwargs.get('stream', False):
                    # Возвращаем асинхронный генератор для стриминга
                    return self.provider.get_streaming_completion(messages, model, **clean_kwargs)
                else:
                    # Обычный запрос
                    result = await self.provider.get_completion(messages, model, **clean_kwargs)
                    
                    # Создаем объект, совместимый с OpenAI API
                    class Usage:
                        def __init__(self, usage_data):
                            self.total_tokens = usage_data.get('total_tokens', 0)
                            self.prompt_tokens = usage_data.get('prompt_tokens', 0)
                            self.completion_tokens = usage_data.get('completion_tokens', 0)
                    
                    class Message:
                        def __init__(self, content):
                            self.content = content
                    
                    class Choice:
                        def __init__(self, content):
                            self.message = Message(content)
                    
                    class Response:
                        def __init__(self, result):
                            self.choices = [Choice(result['content'])]
                            self.usage = Usage(result.get('usage', {}))
                            self.model = result.get('model', model)
                    
                    return Response(result)
        
        def __init__(self, provider: OpenAIProvider):
            self.completions = self.Completions(provider)
    
    @property
    def chat(self):
        return self.ChatCompletion(self.provider)