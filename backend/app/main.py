"""Главный модуль FastAPI приложения AlloyPredictor."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .api.v1 import api_router
from .ml.predictor import get_predictor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения."""
    # Startup
    logger.info("Запуск AlloyPredictor API...")
    logger.info(f"Debug mode: {settings.debug}")

    # Инициализация предиктора (загрузка моделей)
    predictor = get_predictor()
    logger.info(f"Загружено моделей: {len(predictor.models)}")

    yield

    # Shutdown
    logger.info("Остановка AlloyPredictor API...")


# Создание приложения
app = FastAPI(
    title=settings.app_name,
    description="""
## AlloyPredictor API

AI-система для прогнозирования свойств металлических сплавов.

### Возможности:

* **Прогнозирование свойств** - предсказание механических свойств по химическому составу
* **Оптимизация состава** - подбор оптимального состава под целевые свойства
* **Справочник марок** - база данных распространённых марок сталей

### Прогнозируемые свойства:

- Предел прочности (UTS)
- Предел текучести (YS)
- Удлинение
- Твёрдость (HRC/HV)
- Модуль Юнга
- Коррозионная стойкость
- Свариваемость
- Магнитные свойства
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": settings.api_v1_prefix,
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    predictor = get_predictor()
    return {
        "status": "healthy",
        "models_loaded": len(predictor.models),
        "debug": settings.debug,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
