import asyncio
import logging
from typing import List, Optional, Dict, Type
from datetime import datetime

from models.schemas import NewsSource
from services.base_parser import BaseNewsParser
from services.medvestnik_parser import MedvestnikParser
from services.ria_parser import RiaParser
from services.aig_parser import AigParser
from services.remedium_parser import RemediumParser
from services.rbc_medical_parser import RBCMedicalParser


logger = logging.getLogger(__name__)

class NewsParserManager:
    """Менеджер для управления различными парсерами новостей"""
    
    def __init__(self):
        self._parsers: Dict[str, BaseNewsParser] = {}
        self._initialize_parsers()
    
    def _initialize_parsers(self):
        """Инициализация всех доступных парсеров"""
        try:
            # Регистрируем парсеры
            self._parsers = {}
            self._parsers['medvestnik'] = MedvestnikParser()
            self._parsers['ria'] = RiaParser()
            self._parsers['aig'] = AigParser()
            self._parsers['remedium'] = RemediumParser()
            self._parsers['rbc_medical'] = RBCMedicalParser()
            
            logger.info(f"Initialized {len(self._parsers)} news parsers: {list(self._parsers.keys())}")
        except Exception as e:
            logger.error(f"Error initializing parsers: {e}")
    
    async def _ensure_parser_session(self, parser: BaseNewsParser):
        """Обеспечивает наличие активной HTTP сессии у парсера"""
        if not parser.session or parser.session.closed:
            await parser.__aenter__()
    
    def get_available_sources(self) -> List[str]:
        """Получение списка доступных источников новостей"""
        return list(self._parsers.keys())
    
    def get_parser(self, source: str) -> Optional[BaseNewsParser]:
        """Получение парсера по названию источника"""
        return self._parsers.get(source)
    
    async def parse_news_from_source(
        self, 
        source: str, 
        max_articles: int = 50, 
        date_filter: Optional[str] = None, 
        fetch_full_content: bool = True
    ) -> List[NewsSource]:
        """Парсинг новостей из конкретного источника"""
        print(f"DEBUG: parse_news_from_source called for source: {source}")
        parser = self.get_parser(source)
        if not parser:
            print(f"DEBUG: Parser for source '{source}' not found")
            logger.error(f"Parser for source '{source}' not found")
            return []
        
        print(f"DEBUG: Found parser for {source}: {type(parser).__name__}")
        
        try:
            # Обеспечиваем наличие активной сессии
            await self._ensure_parser_session(parser)
            print(f"DEBUG: Session ensured for {source}")
            
            logger.info(f"Starting news parsing from {source}")
            print(f"DEBUG: Calling parse_news_list for {source} with max_articles={max_articles}")
            news_items = await parser.parse_news_list(
                max_articles=max_articles,
                date_filter=date_filter,
                fetch_full_content=fetch_full_content
            )
            print(f"DEBUG: parse_news_list returned {len(news_items)} items for {source}")
            logger.info(f"Successfully parsed {len(news_items)} articles from {source}")
            return news_items
        except Exception as e:
            print(f"DEBUG: Exception in parse_news_from_source for {source}: {e}")
            logger.error(f"Error parsing news from {source}: {e}")
            return []
    
    async def parse_news_from_multiple_sources(
        self, 
        sources: List[str], 
        max_articles_per_source: int = 10, 
        date_filter: Optional[str] = None, 
        fetch_full_content: bool = True
    ) -> Dict[str, List[NewsSource]]:
        """Парсинг новостей из нескольких источников параллельно"""
        print(f"DEBUG: parse_news_from_multiple_sources called with sources: {sources}")
        results = {}
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        valid_sources = []
        
        for source in sources:
            if source in self._parsers:
                print(f"DEBUG: Adding task for source: {source}")
                task = self.parse_news_from_source(
                    source=source,
                    max_articles=max_articles_per_source,
                    date_filter=date_filter,
                    fetch_full_content=fetch_full_content
                )
                tasks.append(task)
                valid_sources.append(source)
            else:
                print(f"DEBUG: Unknown source: {source}")
                logger.warning(f"Unknown source: {source}")
                results[source] = []
        
        print(f"DEBUG: Created {len(tasks)} tasks for sources: {valid_sources}")
        
        # Выполняем все задачи параллельно
        if tasks:
            try:
                print(f"DEBUG: Starting parallel execution of {len(tasks)} tasks")
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
                print(f"DEBUG: Parallel execution completed, got {len(results_list)} results")
                
                for i, result in enumerate(results_list):
                    source = valid_sources[i]
                    if isinstance(result, Exception):
                        print(f"DEBUG: Exception for {source}: {result}")
                        logger.error(f"Error parsing {source}: {result}")
                        results[source] = []
                    else:
                        print(f"DEBUG: Success for {source}: {len(result)} articles")
                        results[source] = result
            except Exception as e:
                print(f"DEBUG: Error in parallel parsing: {e}")
                logger.error(f"Error in parallel parsing: {e}")
                for source in valid_sources:
                    results[source] = []
        
        print(f"DEBUG: Final results: {[(k, len(v)) for k, v in results.items()]}")
        return results
    
    async def parse_all_sources(
        self, 
        max_articles_per_source: int = 10, 
        date_filter: Optional[str] = None, 
        fetch_full_content: bool = True
    ) -> Dict[str, List[NewsSource]]:
        """Парсинг новостей из всех доступных источников"""
        return await self.parse_news_from_multiple_sources(
            sources=list(self._parsers.keys()),
            max_articles_per_source=max_articles_per_source,
            date_filter=date_filter,
            fetch_full_content=fetch_full_content
        )
    
    async def get_combined_news(
        self, 
        sources: Optional[List[str]] = None, 
        max_articles_per_source: int = 10, 
        date_filter: Optional[str] = None, 
        fetch_full_content: bool = True,
        sort_by_date: bool = True
    ) -> List[NewsSource]:
        """Получение объединенного списка новостей из выбранных источников"""
        if sources is None:
            sources = list(self._parsers.keys())
        
        # Парсим новости из всех источников
        results = await self.parse_news_from_multiple_sources(
            sources=sources,
            max_articles_per_source=max_articles_per_source,
            date_filter=date_filter,
            fetch_full_content=fetch_full_content
        )
        
        # Объединяем все новости в один список
        combined_news = []
        for source, news_list in results.items():
            combined_news.extend(news_list)
        
        # Сортируем по дате если требуется
        if sort_by_date:
            # Сортируем по числовому таймстемпу, чтобы избежать проблем aware/naive
            def _ts(d):
                try:
                    if not d:
                        return 0
                    # Для aware/naive одинаково используем timestamp()
                    return d.timestamp()
                except Exception:
                    try:
                        return d.replace(tzinfo=None).timestamp() if d else 0
                    except Exception:
                        return 0
            combined_news.sort(key=lambda x: _ts(getattr(x, 'published_date', None)), reverse=True)
        
        return combined_news
    
    async def close_all_parsers(self):
        """Закрытие всех парсеров и освобождение ресурсов"""
        for parser in self._parsers.values():
            try:
                if parser.session and not parser.session.closed:
                    await parser.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing parser: {e}")
        
        logger.info("All parsers closed")
    
    def get_parser_info(self) -> Dict[str, Dict[str, str]]:
        """Получение информации о всех парсерах"""
        info = {}
        for name, parser in self._parsers.items():
            info[name] = {
                'name': parser.source_name,
                'base_url': parser.base_url,
                'status': 'active' if parser.session and not parser.session.closed else 'inactive'
            }
        return info

# Глобальный экземпляр менеджера парсеров
news_parser_manager = NewsParserManager()