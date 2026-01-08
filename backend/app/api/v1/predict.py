"""
API эндпоинты для прогнозирования свойств сплавов.

Эндпоинты:
- POST /predict/ - Полный прогноз (стандартный)
- POST /predict/quick - Быстрый прогноз (простой вход)
- POST /predict/full - Расширенный прогноз всех свойств
- POST /predict/batch - Пакетный прогноз
- POST /predict/optimize - Оптимизация состава
- POST /predict/fatigue - Усталостные свойства
- POST /predict/impact - Ударная вязкость
- POST /predict/corrosion - Коррозионные свойства
- POST /predict/heat-treatment - Термообработка
- POST /predict/wear - Износостойкость
- GET /predict/elements - Список элементов
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List

from ...schemas.composition import CompositionInput, AlloyComposition
from ...schemas.prediction import (
    PredictionResponse,
    FullPredictionResponse,
    QuickPredictionResponse,
    FatigueProperties,
    ImpactProperties,
    CorrosionProperties,
    HeatTreatmentProperties,
    WearProperties,
    OptimizationRequest,
    OptimizationResponse,
)
from ...ml.predictor import get_predictor

router = APIRouter()


@router.post("/", response_model=PredictionResponse)
async def predict_alloy_properties(input_data: CompositionInput) -> PredictionResponse:
    """
    Прогнозирование свойств сплава по химическому составу.

    Входные данные:
    - composition: Химический состав сплава (проценты элементов)
    - heat_treatment: Опционально - тип термообработки
    - temperature_c: Опционально - температура обработки

    Возвращает:
    - mechanical_properties: Механические свойства (прочность, твёрдость, etc.)
    - behavior: Поведение (коррозия, магнетизм, свариваемость)
    - classification: Тип сплава, марка, области применения
    - confidence: Уверенность модели
    """
    try:
        predictor = get_predictor()
        result = predictor.predict(input_data.composition)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка прогнозирования: {str(e)}")


@router.post("/quick", response_model=PredictionResponse)
async def predict_quick(composition: Dict[str, float]) -> PredictionResponse:
    """
    Быстрое прогнозирование - принимает просто словарь с составом.

    Пример:
    ```json
    {"Fe": 97.5, "C": 0.45, "Si": 0.25, "Mn": 0.65}
    ```
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        result = predictor.predict(alloy_composition)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.post("/batch", response_model=list[PredictionResponse])
async def predict_batch(compositions: list[Dict[str, float]]) -> list[PredictionResponse]:
    """
    Пакетное прогнозирование для нескольких составов.

    Максимум 100 составов за запрос.
    """
    if len(compositions) > 100:
        raise HTTPException(status_code=400, detail="Максимум 100 составов за запрос")

    predictor = get_predictor()
    results = []

    for comp in compositions:
        try:
            alloy_composition = AlloyComposition(**comp)
            result = predictor.predict(alloy_composition)
            results.append(result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Ошибка в составе: {str(e)}")

    return results


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_composition(request: OptimizationRequest) -> OptimizationResponse:
    """
    Оптимизация состава сплава под целевые свойства.

    Использует алгоритм дифференциальной эволюции для поиска
    оптимального химического состава.

    Входные данные:
    - target_properties: Целевые свойства
        - min_yield_strength: Минимальный предел текучести (МПа)
        - min_tensile_strength: Минимальный предел прочности (МПа)
        - min_elongation: Минимальное удлинение (%)
        - target_hardness: Целевая твёрдость (HRC)
    - constraints: Ограничения
        - base_element: Базовый элемент (по умолчанию "Fe")
        - forbidden_elements: Список запрещённых элементов
        - max_cost: Максимальная стоимость ("low", "medium", "high")
        - min_elements: Минимальные значения элементов
        - max_elements: Максимальные значения элементов
    - num_alternatives: Количество альтернативных вариантов (1-10)

    Возвращает:
    - optimal_composition: Оптимальный состав (словарь элемент: процент)
    - predicted_properties: Прогнозируемые механические свойства
    - fitness_score: Оценка соответствия целям (0-1)
    - alternatives: Альтернативные составы с их свойствами
    """
    from ...ml.optimizer import get_optimizer, OptimizationConfig

    try:
        # Парсим целевые свойства
        target = request.target_properties
        constraints = request.constraints

        # Создаём конфигурацию оптимизации
        config = OptimizationConfig(
            target_yield_strength=target.get("min_yield_strength"),
            target_tensile_strength=target.get("min_tensile_strength"),
            target_elongation=target.get("min_elongation"),
            target_hardness=target.get("target_hardness"),
            base_element=constraints.base_element,
            forbidden_elements=constraints.forbidden_elements,
            max_cost_level=constraints.max_cost or "high",
            min_elements=constraints.min_elements,
            max_elements=constraints.max_elements,
            num_alternatives=request.num_alternatives,
        )

        # Запускаем оптимизацию
        optimizer = get_optimizer()
        result = optimizer.optimize(config)

        return OptimizationResponse(
            optimal_composition=result["optimal_composition"],
            predicted_properties=result["predicted_properties"],
            fitness_score=result["fitness_score"],
            alternatives=result["alternatives"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка оптимизации: {str(e)}"
        )


@router.get("/elements")
async def get_supported_elements() -> Dict:
    """Получить список поддерживаемых элементов и их ограничения."""
    return {
        "elements": [
            {"symbol": "Fe", "name": "Железо", "max_percent": 100},
            {"symbol": "C", "name": "Углерод", "max_percent": 5},
            {"symbol": "Si", "name": "Кремний", "max_percent": 5},
            {"symbol": "Mn", "name": "Марганец", "max_percent": 20},
            {"symbol": "Cr", "name": "Хром", "max_percent": 30},
            {"symbol": "Ni", "name": "Никель", "max_percent": 40},
            {"symbol": "Mo", "name": "Молибден", "max_percent": 10},
            {"symbol": "V", "name": "Ванадий", "max_percent": 5},
            {"symbol": "W", "name": "Вольфрам", "max_percent": 20},
            {"symbol": "Co", "name": "Кобальт", "max_percent": 30},
            {"symbol": "Ti", "name": "Титан", "max_percent": 5},
            {"symbol": "Al", "name": "Алюминий", "max_percent": 100},
            {"symbol": "Cu", "name": "Медь", "max_percent": 10},
            {"symbol": "Nb", "name": "Ниобий", "max_percent": 5},
            {"symbol": "P", "name": "Фосфор", "max_percent": 1},
            {"symbol": "S", "name": "Сера", "max_percent": 1},
            {"symbol": "N", "name": "Азот", "max_percent": 1},
        ]
    }


# =============================================================================
# РАСШИРЕННЫЕ ЭНДПОИНТЫ ДЛЯ СПЕЦИФИЧЕСКИХ СВОЙСТВ
# =============================================================================

@router.post("/full", response_model=FullPredictionResponse)
async def predict_full_properties(composition: Dict[str, float]) -> FullPredictionResponse:
    """
    Расширенный прогноз ВСЕХ свойств сплава.

    Возвращает полный набор характеристик:
    - mechanical_properties: Механические свойства (σт, σв, δ, HRC)
    - fatigue_properties: Усталостные свойства (предел выносливости)
    - impact_properties: Ударная вязкость (KCV, переходная температура)
    - corrosion_properties: Коррозионные свойства (PREN, скорость коррозии)
    - heat_treatment_properties: Термообработка (Ac1, Ac3, Ms, CE)
    - wear_properties: Износостойкость (индекс износа)
    - behavior: Качественные характеристики
    - classification: Тип сплава и применение

    Пример запроса:
    ```json
    {"Fe": 68, "C": 0.12, "Si": 0.8, "Mn": 2, "Cr": 18, "Ni": 10}
    ```
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        result = predictor.predict_full(alloy_composition)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.post("/fatigue", response_model=FatigueProperties)
async def predict_fatigue_properties(composition: Dict[str, float]) -> FatigueProperties:
    """
    Прогноз усталостных свойств.

    Рассчитывает:
    - fatigue_limit_mpa: Предел выносливости σ-1 (МПа)
    - fatigue_ratio: Коэффициент усталости σ-1/σв
    - basquin_exponent: Показатель уравнения Басквина

    Используемые формулы:
    - σ-1 ≈ k × σв, где k = 0.40-0.50 для сталей
    - Уравнение Басквина: Δσ/2 = σ'f × (2Nf)^b

    Пример:
    ```json
    {"Fe": 97.5, "C": 0.45, "Si": 0.25, "Mn": 0.65}
    ```
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        comp_dict = alloy_composition.model_dump()

        # Сначала получаем механические свойства для расчёта усталости
        mech = predictor.predict(alloy_composition).mechanical_properties

        result = predictor.predict_fatigue(comp_dict, mech.tensile_strength_mpa)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.post("/impact", response_model=ImpactProperties)
async def predict_impact_properties(composition: Dict[str, float]) -> ImpactProperties:
    """
    Прогноз ударной вязкости.

    Рассчитывает:
    - impact_energy_j: Работа удара KV (Дж)
    - kcv_j_cm2: Ударная вязкость KCV (Дж/см²)
    - transition_temp_c: Температура вязко-хрупкого перехода (°C)

    Используемые формулы (Пикеринг):
    Ttr = -19 + 44×Si + 700×√P + 2.2×√(100×C) - 11.5×√Ni

    Стандарты: ГОСТ 9454-78, ISO 148-1, ASTM E23
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        comp_dict = alloy_composition.model_dump()
        result = predictor.predict_impact(comp_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.post("/corrosion", response_model=CorrosionProperties)
async def predict_corrosion_properties(composition: Dict[str, float]) -> CorrosionProperties:
    """
    Прогноз коррозионных свойств.

    Рассчитывает:
    - pren: PREN (Pitting Resistance Equivalent Number)
    - cpt_c: Критическая температура питтингообразования (°C)
    - corrosion_rate_mm_year: Скорость общей коррозии (мм/год)

    Формулы:
    - PREN = Cr + 3.3×Mo + 16×N
    - CPT ≈ 2.5 × PREN - 30

    Стандарты: ISO 17864, ASTM G48
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        comp_dict = alloy_composition.model_dump()
        result = predictor.predict_corrosion(comp_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.post("/heat-treatment", response_model=HeatTreatmentProperties)
async def predict_heat_treatment_properties(
    composition: Dict[str, float]
) -> HeatTreatmentProperties:
    """
    Прогноз свойств термообработки.

    Рассчитывает:
    - carbon_equivalent: Углеродный эквивалент CE (IIW)
    - ac1_temp_c: Температура Ac1 (°C)
    - ac3_temp_c: Температура Ac3 (°C)
    - ms_temp_c: Температура Ms (°C)
    - quench_hardness_hrc: Твёрдость после закалки (HRC)

    Эмпирические формулы (Andrews, 1965):
    - Ac1 = 727 - 10.7×Mn - 16.9×Ni + 29.1×Si + 16.9×Cr + 6.38×W
    - Ac3 = 910 - 203×√C - 15.2×Ni + 44.7×Si + 104×V + 31.5×Mo
    - Ms = 539 - 423×C - 30.4×Mn - 17.7×Ni - 12.1×Cr - 7.5×Mo

    CE (IIW) = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        comp_dict = alloy_composition.model_dump()
        result = predictor.predict_heat_treatment(comp_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.post("/wear", response_model=WearProperties)
async def predict_wear_properties(composition: Dict[str, float]) -> WearProperties:
    """
    Прогноз износостойкости.

    Рассчитывает:
    - wear_resistance_index: Индекс износостойкости (0-10)
    - mass_loss_mg: Потеря массы при испытании (мг)
    - carbide_volume_percent: Объём карбидной фазы (%)

    Формулы:
    - Wear_index ∝ (HV/200)^1.5 × (1 + V_carbide × 0.02)
    - V_carbide = C×15 + Cr×0.3 + Mo×1 + V×3 + W×0.5

    Стандарты: ASTM G65, ISO 9352
    """
    try:
        alloy_composition = AlloyComposition(**composition)
        predictor = get_predictor()
        comp_dict = alloy_composition.model_dump()

        # Получаем твёрдость для расчёта износа
        mech = predictor.predict(alloy_composition).mechanical_properties
        hardness_hv = mech.hardness_hv or 200

        result = predictor.predict_wear(comp_dict, hardness_hv)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка: {str(e)}")


@router.get("/models-status")
async def get_models_status() -> Dict:
    """
    Получить статус загруженных ML моделей.

    Возвращает информацию о том, какие модели загружены
    и какие категории свойств доступны для прогнозирования.
    """
    predictor = get_predictor()

    return {
        "loaded_models": list(predictor.models.keys()),
        "loaded_categories": predictor.loaded_categories,
        "available_endpoints": {
            "mechanical": "/predict/quick",
            "fatigue": "/predict/fatigue",
            "impact": "/predict/impact",
            "corrosion": "/predict/corrosion",
            "heat_treatment": "/predict/heat-treatment",
            "wear": "/predict/wear",
            "full": "/predict/full",
        },
        "model_categories": predictor.MODEL_CATEGORIES,
    }
