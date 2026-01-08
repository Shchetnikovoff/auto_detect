"""
Схемы для результатов прогнозирования свойств сплавов.

Включает схемы для:
- Механических свойств (прочность, твёрдость, удлинение)
- Усталостных свойств (предел выносливости, циклы до разрушения)
- Ударной вязкости (KCV, переходная температура)
- Коррозионной стойкости (PREN, CPT, скорость коррозии)
- Термообработки (критические температуры, прокаливаемость)
- Износостойкости (индекс износа, потеря массы)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# =============================================================================
# ENUMS - Перечисления для категориальных свойств
# =============================================================================

class CorrosionResistance(str, Enum):
    """Уровень коррозионной стойкости."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Weldability(str, Enum):
    """Свариваемость."""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class AlloyType(str, Enum):
    """Тип сплава."""
    CARBON_STEEL = "carbon_steel"
    LOW_ALLOY_STEEL = "low_alloy_steel"
    STAINLESS_STEEL = "stainless_steel"
    TOOL_STEEL = "tool_steel"
    HIGH_SPEED_STEEL = "high_speed_steel"
    ALUMINUM_ALLOY = "aluminum_alloy"
    TITANIUM_ALLOY = "titanium_alloy"
    NICKEL_ALLOY = "nickel_alloy"
    HIGH_ENTROPY_ALLOY = "high_entropy_alloy"


# =============================================================================
# ОСНОВНЫЕ СВОЙСТВА - Механические характеристики
# =============================================================================

class MechanicalProperties(BaseModel):
    """
    Механические свойства сплава.

    Основные характеристики прочности и пластичности материала,
    определяемые при статических испытаниях на растяжение.
    """

    yield_strength_mpa: float = Field(..., ge=0, description="Предел текучести σ0.2 (МПа)")
    tensile_strength_mpa: float = Field(..., ge=0, description="Предел прочности σв (МПа)")
    elongation_percent: float = Field(..., ge=0, le=100, description="Относительное удлинение δ (%)")
    hardness_hrc: Optional[float] = Field(None, ge=0, le=70, description="Твёрдость по Роквеллу (HRC)")
    hardness_hv: Optional[float] = Field(None, ge=0, description="Твёрдость по Виккерсу (HV)")
    youngs_modulus_gpa: float = Field(..., ge=0, description="Модуль упругости E (ГПа)")
    density_g_cm3: Optional[float] = Field(None, ge=0, description="Плотность ρ (г/см³)")


# =============================================================================
# УСТАЛОСТНЫЕ СВОЙСТВА - Сопротивление циклическим нагрузкам
# =============================================================================

class FatigueProperties(BaseModel):
    """
    Усталостные свойства сплава.

    Характеристики сопротивления материала циклическим (повторно-переменным)
    нагрузкам. Определяются по ГОСТ 25.502-79, ASTM E466.

    Эмпирические зависимости:
    - Предел выносливости: σ-1 ≈ k × σв, где k = 0.40-0.50 для сталей
    - Уравнение Басквина: Δσ/2 = σ'f × (2Nf)^b, где b ≈ -0.05...-0.12
    """

    fatigue_limit_mpa: float = Field(
        ..., ge=0,
        description="Предел выносливости σ-1 (МПа) - напряжение, при котором материал выдерживает 10^7 циклов"
    )
    fatigue_ratio: float = Field(
        ..., ge=0, le=1,
        description="Коэффициент усталости σ-1/σв (обычно 0.4-0.5 для сталей)"
    )
    cycles_to_failure_log: Optional[float] = Field(
        None,
        description="Логарифм числа циклов до разрушения log10(Nf) при заданном напряжении"
    )
    basquin_exponent: Optional[float] = Field(
        None, le=0,
        description="Показатель уравнения Басквина b (отрицательное значение, обычно -0.05...-0.12)"
    )
    endurance_limit_cycles: float = Field(
        default=1e7,
        description="База испытаний (число циклов для определения предела выносливости)"
    )


# =============================================================================
# УДАРНАЯ ВЯЗКОСТЬ - Сопротивление динамическим нагрузкам
# =============================================================================

class ImpactProperties(BaseModel):
    """
    Ударная вязкость сплава.

    Характеристики сопротивления материала ударным нагрузкам.
    Определяются по ГОСТ 9454-78, ISO 148-1, ASTM E23 (испытание по Шарпи).

    Эмпирические зависимости (формула Пикеринга):
    Ttr = -19 + 44×Si + 700×√P + 2.2×√(100×C) - 11.5×√Ni (°C)

    Где Ttr - температура вязко-хрупкого перехода.
    """

    impact_energy_j: float = Field(
        ..., ge=0,
        description="Работа удара KV (Дж) - энергия, поглощённая при разрушении образца"
    )
    kcv_j_cm2: float = Field(
        ..., ge=0,
        description="Ударная вязкость KCV (Дж/см²) - работа удара на единицу площади сечения"
    )
    transition_temp_c: float = Field(
        ...,
        description="Температура вязко-хрупкого перехода T50 (°C)"
    )
    upper_shelf_energy_j: Optional[float] = Field(
        None, ge=0,
        description="Верхняя полка ударной вязкости (Дж) - энергия при вязком разрушении"
    )
    lower_shelf_energy_j: Optional[float] = Field(
        None, ge=0,
        description="Нижняя полка ударной вязкости (Дж) - энергия при хрупком разрушении"
    )
    ductile_fraction_percent: Optional[float] = Field(
        None, ge=0, le=100,
        description="Доля вязкой составляющей в изломе (%)"
    )


# =============================================================================
# КОРРОЗИОННАЯ СТОЙКОСТЬ - Количественные характеристики
# =============================================================================

class CorrosionProperties(BaseModel):
    """
    Коррозионные свойства сплава (количественные).

    Характеристики стойкости к электрохимической коррозии.
    Определяются по ГОСТ 9.912-89, ISO 17864, ASTM G48.

    Эмпирические зависимости:
    - PREN = Cr + 3.3×Mo + 16×N (индекс питтинговой стойкости)
    - CPT ≈ 2.5 × PREN - 30 (критическая температура питтинга, °C)
    """

    pren: float = Field(
        ..., ge=0,
        description="PREN (Pitting Resistance Equivalent Number) - индекс стойкости к питтинговой коррозии"
    )
    cpt_c: Optional[float] = Field(
        None,
        description="CPT (Critical Pitting Temperature) - критическая температура питтингообразования (°C)"
    )
    corrosion_rate_mm_year: float = Field(
        ..., ge=0,
        description="Скорость общей коррозии (мм/год) в стандартных условиях"
    )
    passivation_potential_v: Optional[float] = Field(
        None,
        description="Потенциал пассивации (В) относительно стандартного водородного электрода"
    )
    pitting_potential_v: Optional[float] = Field(
        None,
        description="Потенциал питтингообразования (В)"
    )


# =============================================================================
# ТЕРМООБРАБОТКА - Критические температуры и прокаливаемость
# =============================================================================

class HeatTreatmentProperties(BaseModel):
    """
    Свойства термообработки сплава.

    Критические температуры фазовых превращений и характеристики
    закаливаемости. Определяются по ГОСТ 5657-69, ISO 642.

    Эмпирические формулы (Andrews, 1965):
    - Ac1 = 727 - 10.7×Mn - 16.9×Ni + 29.1×Si + 16.9×Cr + 6.38×W (°C)
    - Ac3 = 910 - 203×√C - 15.2×Ni + 44.7×Si + 104×V + 31.5×Mo (°C)
    - Ms = 539 - 423×C - 30.4×Mn - 17.7×Ni - 12.1×Cr - 7.5×Mo (°C)

    Углеродный эквивалент (IIW):
    CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15
    """

    carbon_equivalent: float = Field(
        ..., ge=0,
        description="Углеродный эквивалент CE (IIW) - показатель закаливаемости и свариваемости"
    )
    ac1_temp_c: float = Field(
        ...,
        description="Температура Ac1 (°C) - начало α→γ превращения при нагреве"
    )
    ac3_temp_c: float = Field(
        ...,
        description="Температура Ac3 (°C) - конец α→γ превращения при нагреве"
    )
    ms_temp_c: float = Field(
        ...,
        description="Температура Ms (°C) - начало мартенситного превращения при охлаждении"
    )
    mf_temp_c: Optional[float] = Field(
        None,
        description="Температура Mf (°C) - конец мартенситного превращения"
    )
    quench_hardness_hrc: Optional[float] = Field(
        None, ge=0, le=70,
        description="Максимальная твёрдость после закалки (HRC)"
    )
    hardenability_mm: Optional[float] = Field(
        None, ge=0,
        description="Прокаливаемость по Джомини (мм) - глубина закалённого слоя"
    )
    recommended_quench_temp_c: Optional[float] = Field(
        None,
        description="Рекомендуемая температура закалки (°C)"
    )
    recommended_temper_temp_c: Optional[float] = Field(
        None,
        description="Рекомендуемая температура отпуска (°C)"
    )


# =============================================================================
# ИЗНОСОСТОЙКОСТЬ - Сопротивление абразивному износу
# =============================================================================

class WearProperties(BaseModel):
    """
    Износостойкость сплава.

    Характеристики сопротивления абразивному износу.
    Определяются по ГОСТ 23.208-79, ISO 9352, ASTM G65.

    Эмпирические зависимости:
    - Wear_index ∝ (HV/200)^1.5 × (1 + V_carbide × 0.02)
    - V_carbide = C×15 + Cr×0.3 + Mo×1 + V×3 + W×0.5 (объём карбидов)
    """

    wear_resistance_index: float = Field(
        ..., ge=0,
        description="Индекс износостойкости (относительная величина, больше = лучше)"
    )
    mass_loss_mg: Optional[float] = Field(
        None, ge=0,
        description="Потеря массы при стандартном испытании (мг)"
    )
    volume_loss_mm3: Optional[float] = Field(
        None, ge=0,
        description="Объёмный износ при стандартном испытании (мм³)"
    )
    carbide_volume_percent: Optional[float] = Field(
        None, ge=0, le=50,
        description="Объёмная доля карбидной фазы (%)"
    )
    abrasion_resistance_class: Optional[str] = Field(
        None,
        description="Класс абразивной стойкости (low/medium/high/very_high)"
    )


class AlloyBehavior(BaseModel):
    """Поведение сплава в различных условиях."""

    corrosion_resistance: CorrosionResistance = Field(..., description="Коррозионная стойкость")
    magnetic: bool = Field(..., description="Магнитные свойства")
    weldability: Weldability = Field(..., description="Свариваемость")
    heat_treatable: bool = Field(..., description="Возможность термообработки")
    oxidation_resistance: Optional[str] = Field(None, description="Стойкость к окислению")
    wear_resistance: Optional[str] = Field(None, description="Износостойкость")


class AlloyClassification(BaseModel):
    """Классификация и рекомендации по применению."""

    alloy_type: AlloyType = Field(..., description="Тип сплава")
    grade: Optional[str] = Field(None, description="Ближайшая марка стали (AISI/ГОСТ)")
    applications: list[str] = Field(default_factory=list, description="Области применения")
    similar_alloys: list[str] = Field(default_factory=list, description="Похожие сплавы")


# =============================================================================
# ОТВЕТЫ API - Структуры ответов для различных запросов
# =============================================================================

class PredictionResponse(BaseModel):
    """
    Полный ответ с прогнозом свойств сплава.

    Содержит все прогнозируемые характеристики материала:
    - Механические свойства (обязательно)
    - Усталостные свойства (опционально)
    - Ударная вязкость (опционально)
    - Коррозионные свойства (опционально)
    - Свойства термообработки (опционально)
    - Износостойкость (опционально)
    """

    # Основные свойства (всегда присутствуют)
    mechanical_properties: MechanicalProperties
    behavior: AlloyBehavior
    classification: AlloyClassification

    # Расширенные свойства (опциональные, требуют дополнительных моделей)
    fatigue_properties: Optional[FatigueProperties] = Field(
        None, description="Усталостные свойства"
    )
    impact_properties: Optional[ImpactProperties] = Field(
        None, description="Ударная вязкость"
    )
    corrosion_properties: Optional[CorrosionProperties] = Field(
        None, description="Коррозионные свойства (количественные)"
    )
    heat_treatment_properties: Optional[HeatTreatmentProperties] = Field(
        None, description="Свойства термообработки"
    )
    wear_properties: Optional[WearProperties] = Field(
        None, description="Износостойкость"
    )

    # Метаданные
    confidence: float = Field(..., ge=0, le=1, description="Уверенность модели (0-1)")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения")
    models_used: List[str] = Field(
        default_factory=list,
        description="Список использованных моделей для прогноза"
    )


class QuickPredictionResponse(BaseModel):
    """
    Быстрый ответ только с основными свойствами.

    Используется для эндпоинта /predict/quick - возвращает только
    механические свойства, поведение и классификацию без дополнительных
    характеристик (усталость, удар, коррозия и т.д.).
    """

    mechanical_properties: MechanicalProperties
    behavior: AlloyBehavior
    classification: AlloyClassification
    confidence: float = Field(..., ge=0, le=1, description="Уверенность модели")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения")


class FullPredictionResponse(BaseModel):
    """
    Полный ответ со всеми доступными свойствами.

    Используется для эндпоинта /predict/full - возвращает все
    прогнозируемые характеристики материала.
    """

    mechanical_properties: MechanicalProperties
    fatigue_properties: FatigueProperties
    impact_properties: ImpactProperties
    corrosion_properties: CorrosionProperties
    heat_treatment_properties: HeatTreatmentProperties
    wear_properties: WearProperties
    behavior: AlloyBehavior
    classification: AlloyClassification
    confidence: float = Field(..., ge=0, le=1, description="Средняя уверенность моделей")
    warnings: List[str] = Field(default_factory=list, description="Предупреждения")
    models_used: List[str] = Field(default_factory=list, description="Использованные модели")


class OptimizationConstraints(BaseModel):
    """Ограничения для оптимизации состава."""

    base_element: str = Field(default="Fe", description="Базовый элемент")
    forbidden_elements: list[str] = Field(default_factory=list, description="Запрещённые элементы")
    max_cost: Optional[str] = Field(None, description="Максимальная стоимость (low/medium/high)")
    min_elements: dict[str, float] = Field(default_factory=dict, description="Минимальные значения элементов")
    max_elements: dict[str, float] = Field(default_factory=dict, description="Максимальные значения элементов")


class OptimizationRequest(BaseModel):
    """Запрос на оптимизацию состава."""

    target_properties: dict[str, float] = Field(
        ...,
        description="Целевые свойства (min_yield_strength, min_tensile_strength, etc.)"
    )
    constraints: OptimizationConstraints = Field(
        default_factory=OptimizationConstraints,
        description="Ограничения"
    )
    num_alternatives: int = Field(default=3, ge=1, le=10, description="Количество альтернатив")


class OptimizationResponse(BaseModel):
    """Ответ с оптимальным составом."""

    optimal_composition: dict[str, float] = Field(..., description="Оптимальный состав")
    predicted_properties: MechanicalProperties
    fitness_score: float = Field(..., description="Оценка соответствия целям")
    alternatives: list[dict] = Field(default_factory=list, description="Альтернативные составы")
