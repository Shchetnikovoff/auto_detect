"""
Pytest конфигурация и фикстуры для тестирования AlloyPredictor API.
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Добавляем путь к app в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Фикстура для создания тестового клиента FastAPI."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_steel_45():
    """Состав стали 45 для тестов."""
    return {
        "Fe": 97.5,
        "C": 0.45,
        "Si": 0.25,
        "Mn": 0.65
    }


@pytest.fixture
def sample_stainless_steel():
    """Состав нержавеющей стали 12Х18Н10Т для тестов."""
    return {
        "Fe": 68.0,
        "C": 0.12,
        "Si": 0.8,
        "Mn": 2.0,
        "Cr": 18.0,
        "Ni": 10.0,
        "Ti": 0.8
    }


@pytest.fixture
def sample_tool_steel():
    """Состав быстрорежущей стали Р6М5 для тестов."""
    return {
        "Fe": 84.0,
        "C": 0.95,
        "Si": 0.3,
        "Mn": 0.35,
        "Cr": 4.0,
        "Mo": 5.0,
        "V": 2.0,
        "W": 6.0
    }
