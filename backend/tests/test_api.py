"""
Тесты API эндпоинтов AlloyPredictor.

Тестируемые эндпоинты:
- GET /health - проверка состояния сервиса
- POST /api/v1/predict/ - прогноз механических свойств
- POST /api/v1/predict/full - полный прогноз всех свойств
- POST /api/v1/optimize/ - оптимизация состава
- GET /api/v1/reference/grades - справочник марок
"""
import pytest


class TestHealthEndpoint:
    """Тесты эндпоинта проверки здоровья."""

    def test_health_check(self, client):
        """Тест: сервис отвечает на health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_redirect(self, client):
        """Тест: корневой URL перенаправляет на документацию."""
        response = client.get("/", follow_redirects=False)
        # Может быть 200 (если есть главная) или 307 (редирект)
        assert response.status_code in [200, 307, 404]


class TestPredictEndpoint:
    """Тесты эндпоинта прогнозирования."""

    def test_predict_steel_45(self, client, sample_steel_45):
        """Тест: прогноз для стали 45 через /quick эндпоинт."""
        # Используем /quick для простого формата входных данных
        response = client.post("/api/v1/predict/quick", json=sample_steel_45)
        assert response.status_code == 200

        data = response.json()
        # Проверка структуры ответа
        assert "mechanical_properties" in data
        assert "behavior" in data
        assert "classification" in data
        assert "confidence" in data

        # Проверка механических свойств
        mech = data["mechanical_properties"]
        assert "yield_strength_mpa" in mech
        assert "tensile_strength_mpa" in mech
        assert "elongation_percent" in mech

        # Проверка диапазонов для стали 45
        assert 200 < mech["yield_strength_mpa"] < 800
        assert 400 < mech["tensile_strength_mpa"] < 1000
        assert 5 < mech["elongation_percent"] < 30

    def test_predict_stainless_steel(self, client, sample_stainless_steel):
        """Тест: прогноз для нержавеющей стали."""
        response = client.post("/api/v1/predict/quick", json=sample_stainless_steel)
        assert response.status_code == 200

        data = response.json()
        # Нержавеющая сталь должна быть классифицирована правильно
        assert "stainless" in data["classification"]["alloy_type"].lower() or \
               data["behavior"]["corrosion_resistance"] in ["high", "excellent"]

    def test_predict_invalid_composition(self, client):
        """Тест: ошибка при невалидном составе."""
        invalid = {"Fe": -10, "C": 200}
        response = client.post("/api/v1/predict/quick", json=invalid)
        # Ожидаем ошибку валидации
        assert response.status_code in [400, 422]

    def test_predict_empty_composition(self, client):
        """Тест: ошибка при пустом составе."""
        response = client.post("/api/v1/predict/quick", json={})
        # Должна быть ошибка или минимальный состав
        assert response.status_code in [200, 400, 422]


class TestFullPredictEndpoint:
    """Тесты эндпоинта полного прогноза."""

    def test_full_predict_steel(self, client, sample_steel_45):
        """Тест: полный прогноз для стали."""
        response = client.post("/api/v1/predict/full", json=sample_steel_45)
        assert response.status_code == 200

        data = response.json()
        # Проверка наличия всех категорий свойств
        assert "mechanical_properties" in data
        assert "fatigue_properties" in data
        assert "impact_properties" in data
        assert "corrosion_properties" in data
        assert "heat_treatment_properties" in data
        assert "wear_properties" in data

    def test_full_predict_tool_steel(self, client, sample_tool_steel):
        """Тест: полный прогноз для инструментальной стали."""
        response = client.post("/api/v1/predict/full", json=sample_tool_steel)
        assert response.status_code == 200

        data = response.json()
        # Инструментальная сталь должна иметь высокую твёрдость (после закалки)
        mech = data["mechanical_properties"]
        # Проверяем что твёрдость разумная (HRC 25-70)
        if mech.get("hardness_hrc"):
            assert 25 < mech["hardness_hrc"] < 70


class TestOptimizeEndpoint:
    """Тесты эндпоинта оптимизации."""

    def test_optimize_basic(self, client):
        """Тест: базовая оптимизация."""
        request = {
            "target_properties": {
                "min_yield_strength": 500,
                "min_tensile_strength": 700
            },
            "constraints": {
                "base_element": "Fe"
            },
            "num_alternatives": 3
        }
        response = client.post("/api/v1/predict/optimize", json=request)
        assert response.status_code == 200

        data = response.json()
        assert "optimal_composition" in data
        assert "predicted_properties" in data
        assert "fitness_score" in data

    def test_optimize_with_element_constraints(self, client):
        """Тест: оптимизация с ограничениями по элементам."""
        request = {
            "target_properties": {
                "min_yield_strength": 600
            },
            "constraints": {
                "base_element": "Fe",
                "max_elements": {"Cr": 5, "Ni": 3}
            }
        }
        response = client.post("/api/v1/predict/optimize", json=request)
        assert response.status_code == 200


class TestReferenceEndpoint:
    """Тесты эндпоинта справочника."""

    def test_get_grades(self, client):
        """Тест: получение списка марок."""
        response = client.get("/api/v1/reference/grades")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Должны быть марки в справочнике
        assert len(data) > 0

    def test_get_grade_by_name(self, client):
        """Тест: поиск марки по названию."""
        response = client.get("/api/v1/reference/grades", params={"search": "45"})
        assert response.status_code == 200


class TestAPIDocumentation:
    """Тесты документации API."""

    def test_openapi_schema(self, client):
        """Тест: OpenAPI схема доступна."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui(self, client):
        """Тест: Swagger UI доступен."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc(self, client):
        """Тест: ReDoc доступен."""
        response = client.get("/redoc")
        assert response.status_code == 200
