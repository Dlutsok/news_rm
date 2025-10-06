#!/usr/bin/env python3
"""
Скрипт для автоматической публикации запланированных новостей
Запускается через cron каждую минуту
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Добавляем путь к backend модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.scheduler import publication_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/logs/publication_cron.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция обработки запланированных публикаций"""
    try:
        logger.info("=" * 60)
        logger.info(f"Starting scheduled publications check at {datetime.now()}")

        # Обрабатываем запланированные публикации
        published_count = await publication_scheduler.process_scheduled_publications()

        if published_count > 0:
            logger.info(f"Successfully published {published_count} articles")
        else:
            logger.info("No articles ready for publication")

        logger.info("Scheduled publications check completed")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error in publication cron job: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
