"""
Модуль прогнозирования свойств сплавов.

Поддерживает прогнозирование:
- Механических свойств (σт, σв, δ, HRC/HV)
- Усталостных свойств (предел выносливости, коэффициент усталости)
- Ударной вязкости (KCV, переходная температура)
- Коррозионных свойств (PREN, CPT, скорость коррозии)
- Термообработки (Ac1, Ac3, Ms, CE, твёрдость после закалки)
- Износостойкости (индекс износа, потеря массы)

Использует обученные модели из директории models/ или эмпирические формулы
при отсутствии моделей.
"""

import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import logging
import math

from .feature_engineering import get_all_features, calculate_physical_features
from ..schemas.composition import AlloyComposition
from ..schemas.prediction import (
    MechanicalProperties,
    FatigueProperties,
    ImpactProperties,
    CorrosionProperties,
    HeatTreatmentProperties,
    WearProperties,
    AlloyBehavior,
    AlloyClassification,
    PredictionResponse,
    FullPredictionResponse,
    CorrosionResistance,
    Weldability,
    AlloyType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Константы для эмпирических формул
# =============================================================================

# Коэффициенты для расчёта усталостных свойств
FATIGUE_RATIO_RANGE = (0.40, 0.50)  # σ-1/σв для сталей
BASQUIN_EXPONENT_RANGE = (-0.12, -0.05)  # b для уравнения Басквина

# Стандартные значения для ударной вязкости
STANDARD_TEST_TEMPERATURE = 20  # °C
STANDARD_SPECIMEN_AREA = 0.8  # см²


class AlloyPredictor:
    """
    Класс для прогнозирования свойств сплавов.

    Загружает обученные ML модели и использует их для прогнозирования
    механических, усталостных, коррозионных и других свойств.
    При отсутствии моделей использует эмпирические формулы.

    Attributes:
        models_dir: Директория с файлами моделей (.pkl)
        models: Словарь загруженных моделей {name: model}
        scalers: Словарь скейлеров для нормализации {name: scaler}
        metadata: Метаданные моделей (feature_names и др.)
    """

    # Список всех моделей по категориям
    MODEL_CATEGORIES = {
        "mechanical": ["yield_strength", "tensile_strength", "elongation", "hardness"],
        "fatigue": ["fatigue_limit"],
        "impact": ["impact_energy", "transition_temp"],
        "corrosion": ["pren", "corrosion_rate"],
        "heat_treatment": ["ac1_temp", "ac3_temp", "ms_temp", "quench_hardness"],
        "wear": ["wear_index"],
    }

    def __init__(self, models_dir: Optional[Path] = None):
        """
        Инициализация предиктора.

        Args:
            models_dir: Директория с обученными моделями.
                        По умолчанию: ./models относительно этого файла.
        """
        self.models_dir = models_dir or Path(__file__).parent / "models"
        self.models: Dict = {}
        self.scalers: Dict = {}
        self.metadata: Dict = {}
        self.loaded_categories: List[str] = []
        self._load_models()

    def _load_models(self):
        """
        Загрузить обученные модели и scalers.

        Загружает модели для всех категорий свойств:
        - mechanical: yield_strength, tensile_strength, elongation, hardness
        - fatigue: fatigue_limit
        - impact: impact_energy, transition_temp
        - corrosion: pren, corrosion_rate
        - heat_treatment: ac1_temp, ac3_temp, ms_temp, quench_hardness
        - wear: wear_index

        Для каждой модели загружается также соответствующий scaler.
        """
        # Собираем все модели из всех категорий
        all_models = []
        for category, names in self.MODEL_CATEGORIES.items():
            all_models.extend(names)

        loaded_count = 0

        for name in all_models:
            model_path = self.models_dir / f"{name}_model.pkl"
            scaler_path = self.models_dir / f"{name}_scaler.pkl"

            # Загрузка модели
            if model_path.exists():
                try:
                    self.models[name] = joblib.load(model_path)
                    logger.info(f"Загружена модель: {name}")
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"Ошибка загрузки модели {name}: {e}")
            else:
                logger.debug(f"Модель не найдена: {model_path}")

            # Загрузка scaler
            if scaler_path.exists():
                try:
                    self.scalers[name] = joblib.load(scaler_path)
                    logger.debug(f"Загружен scaler: {name}")
                except Exception as e:
                    logger.warning(f"Ошибка загрузки scaler {name}: {e}")

        # Определяем какие категории загружены
        for category, names in self.MODEL_CATEGORIES.items():
            if any(name in self.models for name in names):
                self.loaded_categories.append(category)

        logger.info(f"Загружено {loaded_count} моделей. Категории: {self.loaded_categories}")

        # Загрузка метаданных
        metadata_path = self.models_dir / "metadata.pkl"
        if metadata_path.exists():
            try:
                self.metadata = joblib.load(metadata_path)
                logger.info(f"Загружены метаданные: {self.metadata.get('feature_names', [])}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки метаданных: {e}")

    def _estimate_properties_by_rules(
        self, composition: Dict[str, float]
    ) -> Tuple[MechanicalProperties, float]:
        """
        Оценка свойств на основе эмпирических правил (когда нет ML модели).

        Основано на формулах из металловедения.
        """
        C = composition.get("C", 0)
        Mn = composition.get("Mn", 0)
        Si = composition.get("Si", 0)
        Cr = composition.get("Cr", 0)
        Ni = composition.get("Ni", 0)
        Mo = composition.get("Mo", 0)
        V = composition.get("V", 0)

        # Базовые свойства чистого железа
        base_ys = 250  # МПа
        base_ts = 400  # МПа
        base_el = 30   # %

        # Влияние углерода (основной упрочнитель)
        # Каждые 0.1% C увеличивает прочность примерно на 80 МПа
        carbon_effect_ys = C * 800
        carbon_effect_ts = C * 1000
        carbon_effect_el = -C * 25  # Снижает пластичность

        # Влияние легирующих элементов
        # Mn: упрочнение + повышение ударной вязкости
        mn_effect_ys = Mn * 30
        mn_effect_ts = Mn * 40

        # Cr: повышение прокаливаемости и коррозионной стойкости
        cr_effect_ys = Cr * 20
        cr_effect_ts = Cr * 25

        # Ni: повышение ударной вязкости и коррозионной стойкости
        ni_effect_ys = Ni * 15
        ni_effect_ts = Ni * 20

        # Mo: повышение жаропрочности
        mo_effect_ys = Mo * 40
        mo_effect_ts = Mo * 50

        # V: измельчение зерна, повышение прочности
        v_effect_ys = V * 100
        v_effect_ts = V * 120

        # Si: повышение прочности, снижение пластичности
        si_effect_ys = Si * 80
        si_effect_ts = Si * 100
        si_effect_el = -Si * 5

        # Итоговые свойства
        yield_strength = base_ys + carbon_effect_ys + mn_effect_ys + cr_effect_ys + \
                        ni_effect_ys + mo_effect_ys + v_effect_ys + si_effect_ys

        tensile_strength = base_ts + carbon_effect_ts + mn_effect_ts + cr_effect_ts + \
                          ni_effect_ts + mo_effect_ts + v_effect_ts + si_effect_ts

        elongation = max(5, base_el + carbon_effect_el + si_effect_el - Mn * 2 - Cr * 1)

        # Твёрдость по эмпирической формуле
        # HRC ≈ (Rm / 10) - 18 для сталей
        hardness_hrc = max(0, min(65, tensile_strength / 30 - 5))

        # Модуль Юнга (слабо зависит от состава для сталей)
        youngs_modulus = 210 - Ni * 0.5 + Mo * 0.3

        # Плотность
        Al = composition.get("Al", 0)
        W = composition.get("W", 0)
        density = 7.85 - Al * 0.03 + W * 0.05 + Mo * 0.01

        properties = MechanicalProperties(
            yield_strength_mpa=round(yield_strength, 1),
            tensile_strength_mpa=round(tensile_strength, 1),
            elongation_percent=round(elongation, 1),
            hardness_hrc=round(hardness_hrc, 1) if hardness_hrc > 20 else None,
            hardness_hv=round(hardness_hrc * 10 + 200, 0) if hardness_hrc > 0 else None,
            youngs_modulus_gpa=round(youngs_modulus, 1),
            density_g_cm3=round(density, 2),
        )

        # Уверенность ниже для эмпирических расчётов
        confidence = 0.65

        return properties, confidence

    def _predict_behavior(
        self, composition: Dict[str, float], physical_features: Dict[str, float]
    ) -> AlloyBehavior:
        """Определить поведение сплава."""
        Cr = composition.get("Cr", 0)
        Ni = composition.get("Ni", 0)
        C = composition.get("C", 0)
        Mo = composition.get("Mo", 0)

        # Коррозионная стойкость
        if Cr >= 12 and C < 0.1:
            corrosion = CorrosionResistance.VERY_HIGH
        elif Cr >= 10:
            corrosion = CorrosionResistance.HIGH
        elif Cr >= 5 or Ni >= 3:
            corrosion = CorrosionResistance.MEDIUM
        else:
            corrosion = CorrosionResistance.LOW

        # Магнитные свойства
        # Аустенитные стали (Ni > 8%) немагнитны
        magnetic = not (Ni > 8 and Cr > 16)

        # Свариваемость (зависит от углеродного эквивалента)
        ce = physical_features.get("carbon_equivalent", 0)
        if ce < 0.35:
            weldability = Weldability.EXCELLENT
        elif ce < 0.45:
            weldability = Weldability.GOOD
        elif ce < 0.60:
            weldability = Weldability.FAIR
        else:
            weldability = Weldability.POOR

        # Термообрабатываемость
        heat_treatable = C > 0.25 or (Cr > 0 and Mo > 0)

        return AlloyBehavior(
            corrosion_resistance=corrosion,
            magnetic=magnetic,
            weldability=weldability,
            heat_treatable=heat_treatable,
            oxidation_resistance="high" if Cr > 15 else "medium" if Cr > 5 else "low",
            wear_resistance="high" if C > 0.6 or Mo > 1 else "medium" if C > 0.3 else "low",
        )

    def _classify_alloy(self, composition: Dict[str, float]) -> AlloyClassification:
        """Классифицировать сплав по типу и применению."""
        Fe = composition.get("Fe", 0)
        C = composition.get("C", 0)
        Cr = composition.get("Cr", 0)
        Ni = composition.get("Ni", 0)
        Mo = composition.get("Mo", 0)
        W = composition.get("W", 0)
        V = composition.get("V", 0)
        Al = composition.get("Al", 0)
        Ti = composition.get("Ti", 0)

        applications = []
        similar_alloys = []

        # Определение типа
        if Al > 80:
            alloy_type = AlloyType.ALUMINUM_ALLOY
            applications = ["авиация", "автомобилестроение", "строительство"]
            if composition.get("Cu", 0) > 3:
                similar_alloys = ["Д16", "2024"]
            else:
                similar_alloys = ["АМг6", "5083"]

        elif Ti > 80:
            alloy_type = AlloyType.TITANIUM_ALLOY
            applications = ["авиакосмическая промышленность", "медицина", "химическое оборудование"]
            similar_alloys = ["ВТ6", "Ti-6Al-4V"]

        elif Ni > 40:
            alloy_type = AlloyType.NICKEL_ALLOY
            applications = ["жаропрочные детали", "химическое оборудование", "турбины"]
            similar_alloys = ["Inconel 625", "ХН77ТЮР"]

        elif Cr >= 12 and Fe > 50:
            alloy_type = AlloyType.STAINLESS_STEEL
            if Ni > 7:
                applications = ["пищевая промышленность", "медицина", "химическое оборудование"]
                similar_alloys = ["12Х18Н10Т", "AISI 304", "AISI 316"]
            else:
                applications = ["столовые приборы", "автомобильные детали"]
                similar_alloys = ["08Х13", "AISI 410"]

        elif W > 5 or (Mo > 3 and V > 1):
            alloy_type = AlloyType.HIGH_SPEED_STEEL
            applications = ["режущий инструмент", "свёрла", "фрезы"]
            similar_alloys = ["Р18", "Р6М5", "M2"]

        elif C > 0.5 and (Cr > 5 or Mo > 0.5 or V > 0.1):
            alloy_type = AlloyType.TOOL_STEEL
            applications = ["штампы", "пресс-формы", "инструмент"]
            if C > 1.0:
                similar_alloys = ["ШХ15", "У10А"]
            else:
                similar_alloys = ["5ХНМ", "4Х5МФС"]

        elif Cr > 0 or Ni > 0 or Mo > 0:
            alloy_type = AlloyType.LOW_ALLOY_STEEL
            if Cr > 1 and Mo > 0.2:
                applications = ["валы", "шестерни", "болты высокой прочности"]
                similar_alloys = ["40Х", "40ХН", "AISI 4140"]
            else:
                applications = ["конструкции", "машиностроение"]
                similar_alloys = ["09Г2С", "10ХСНД"]

        else:
            alloy_type = AlloyType.CARBON_STEEL
            if C < 0.25:
                applications = ["листовой прокат", "трубы", "проволока"]
                similar_alloys = ["Ст3", "AISI 1020"]
            elif C < 0.5:
                applications = ["валы", "оси", "крепёж"]
                similar_alloys = ["45", "AISI 1045"]
            else:
                applications = ["пружины", "рессоры", "инструмент"]
                similar_alloys = ["65Г", "AISI 1070"]

        # Поиск ближайшей марки
        grade = similar_alloys[0] if similar_alloys else None

        return AlloyClassification(
            alloy_type=alloy_type,
            grade=grade,
            applications=applications,
            similar_alloys=similar_alloys,
        )

    def predict(self, composition: AlloyComposition) -> PredictionResponse:
        """
        Выполнить прогноз свойств сплава.

        Args:
            composition: Химический состав

        Returns:
            Полный прогноз свойств
        """
        # Преобразование в словарь
        comp_dict = composition.model_dump()

        # Расчёт физических признаков
        physical_features = calculate_physical_features(comp_dict)

        # Получить признаки для ML
        features = get_all_features(comp_dict)

        warnings = []

        # Проверка суммы компонентов
        total = composition.total_percent()
        if abs(total - 100) > 5:
            warnings.append(f"Сумма компонентов ({total:.1f}%) значительно отличается от 100%")

        # Прогноз механических свойств
        if self.models and self.scalers:
            # Использовать ML модели
            properties = self._predict_with_ml(comp_dict)
            confidence = 0.85
        else:
            # Использовать эмпирические формулы
            properties, confidence = self._estimate_properties_by_rules(comp_dict)
            warnings.append("Используются эмпирические формулы (ML модели не загружены)")

        # Прогноз поведения
        behavior = self._predict_behavior(comp_dict, physical_features)

        # Классификация
        classification = self._classify_alloy(comp_dict)

        return PredictionResponse(
            mechanical_properties=properties,
            behavior=behavior,
            classification=classification,
            confidence=confidence,
            warnings=warnings,
        )

    def _prepare_ml_features(self, composition: Dict[str, float]) -> np.ndarray:
        """Подготовка признаков для ML моделей (как в train.py)."""
        import pandas as pd

        # Базовые элементы (как в обучении)
        feature_cols = ["Fe", "C", "Si", "Mn", "Cr", "Ni", "Mo", "V"]

        features = {col: composition.get(col, 0) for col in feature_cols}

        # Углеродный эквивалент
        C = composition.get("C", 0)
        Mn = composition.get("Mn", 0)
        Cr = composition.get("Cr", 0)
        Mo = composition.get("Mo", 0)
        V = composition.get("V", 0)
        Ni = composition.get("Ni", 0)

        features["CE"] = C + Mn / 6 + (Cr + Mo + V) / 5
        features["total_alloy"] = Cr + Ni + Mo + V

        # Возвращаем DataFrame с именами колонок
        return pd.DataFrame([features])

    def _predict_with_ml(self, composition: Dict[str, float]) -> MechanicalProperties:
        """Прогноз с использованием ML моделей."""
        X = self._prepare_ml_features(composition)

        predictions = {}

        for name in ["yield_strength", "tensile_strength", "elongation", "hardness"]:
            if name in self.models and name in self.scalers:
                try:
                    X_scaled = self.scalers[name].transform(X)
                    pred = self.models[name].predict(X_scaled)[0]
                    predictions[name] = pred
                except Exception as e:
                    logger.warning(f"Ошибка прогноза {name}: {e}")
                    predictions[name] = None
            else:
                predictions[name] = None

        # Дефолтные значения если модель не сработала
        ys = predictions.get("yield_strength") or 400
        ts = predictions.get("tensile_strength") or 600
        el = predictions.get("elongation") or 20
        hv = predictions.get("hardness") or 200

        # Конвертация HV в HRC (приблизительно)
        hrc = max(0, (hv - 200) / 10) if hv > 200 else None

        return MechanicalProperties(
            yield_strength_mpa=max(100, round(float(ys), 1)),
            tensile_strength_mpa=max(200, round(float(ts), 1)),
            elongation_percent=max(1, min(60, round(float(el), 1))),
            hardness_hrc=round(float(hrc), 1) if hrc and hrc > 20 else None,
            hardness_hv=round(float(hv), 0) if hv else None,
            youngs_modulus_gpa=210.0,
            density_g_cm3=7.85,
        )

    # =========================================================================
    # УСТАЛОСТНЫЕ СВОЙСТВА
    # =========================================================================

    def predict_fatigue(
        self, composition: Dict[str, float], tensile_strength: float
    ) -> FatigueProperties:
        """
        Прогноз усталостных свойств.

        Использует ML модель или эмпирические формулы:
        - σ-1 ≈ k × σв, где k = 0.40-0.50 для сталей
        - Уравнение Басквина: Δσ/2 = σ'f × (2Nf)^b

        Args:
            composition: Химический состав {element: percent}
            tensile_strength: Предел прочности (МПа)

        Returns:
            FatigueProperties с прогнозируемыми усталостными характеристиками
        """
        C = composition.get("C", 0)
        Cr = composition.get("Cr", 0)
        Ni = composition.get("Ni", 0)
        Mo = composition.get("Mo", 0)

        # Попытка использовать ML модель
        if "fatigue_limit" in self.models:
            try:
                X = self._prepare_ml_features(composition)
                X_scaled = self.scalers["fatigue_limit"].transform(X)
                fatigue_limit = float(self.models["fatigue_limit"].predict(X_scaled)[0])
            except Exception as e:
                logger.warning(f"Ошибка ML прогноза fatigue: {e}")
                fatigue_limit = None
        else:
            fatigue_limit = None

        # Эмпирический расчёт если нет ML
        if fatigue_limit is None:
            # Коэффициент усталости зависит от состава
            # Легированные стали имеют более высокий коэффициент
            base_ratio = 0.45
            if Cr > 1 or Ni > 1 or Mo > 0.2:
                base_ratio = 0.48
            if C > 0.5:
                base_ratio = 0.42  # Высокоуглеродистые - хуже

            fatigue_limit = tensile_strength * base_ratio

        fatigue_ratio = fatigue_limit / tensile_strength if tensile_strength > 0 else 0.45

        # Показатель Басквина (зависит от пластичности)
        # Более пластичные стали имеют меньший показатель (ближе к -0.05)
        basquin_b = -0.08
        if Ni > 5:
            basquin_b = -0.06  # Аустенитные - более пластичные
        elif C > 0.6:
            basquin_b = -0.10  # Высокоуглеродистые - более хрупкие

        return FatigueProperties(
            fatigue_limit_mpa=round(fatigue_limit, 1),
            fatigue_ratio=round(fatigue_ratio, 3),
            cycles_to_failure_log=7.0,  # База 10^7 циклов
            basquin_exponent=round(basquin_b, 3),
            endurance_limit_cycles=1e7,
        )

    # =========================================================================
    # УДАРНАЯ ВЯЗКОСТЬ
    # =========================================================================

    def predict_impact(self, composition: Dict[str, float]) -> ImpactProperties:
        """
        Прогноз ударной вязкости.

        Использует ML модель или формулу Пикеринга:
        Ttr = -19 + 44×Si + 700×√P + 2.2×√(100×C) - 11.5×√Ni (°C)

        Args:
            composition: Химический состав

        Returns:
            ImpactProperties с характеристиками ударной вязкости
        """
        C = composition.get("C", 0)
        Si = composition.get("Si", 0)
        Mn = composition.get("Mn", 0)
        P = composition.get("P", 0.02)  # Типичное содержание примеси
        Ni = composition.get("Ni", 0)
        Cr = composition.get("Cr", 0)

        # ML прогноз
        impact_energy = None
        transition_temp = None

        if "impact_energy" in self.models:
            try:
                X = self._prepare_ml_features(composition)
                X_scaled = self.scalers["impact_energy"].transform(X)
                impact_energy = float(self.models["impact_energy"].predict(X_scaled)[0])
            except Exception as e:
                logger.warning(f"Ошибка ML прогноза impact_energy: {e}")

        if "transition_temp" in self.models:
            try:
                X = self._prepare_ml_features(composition)
                X_scaled = self.scalers["transition_temp"].transform(X)
                transition_temp = float(self.models["transition_temp"].predict(X_scaled)[0])
            except Exception as e:
                logger.warning(f"Ошибка ML прогноза transition_temp: {e}")

        # Эмпирические формулы
        if transition_temp is None:
            # Формула Пикеринга для температуры перехода
            transition_temp = (
                -19 +
                44 * Si +
                700 * math.sqrt(max(0, P)) +
                2.2 * math.sqrt(100 * C) -
                11.5 * math.sqrt(max(0, Ni)) -
                5 * Mn  # Mn снижает переходную температуру
            )

        if impact_energy is None:
            # Базовая ударная вязкость при 20°C
            # Зависит от состава - никель повышает, углерод снижает
            base_kcv = 150  # Дж/см² для мягкой стали

            # Влияние элементов
            base_kcv += Ni * 10  # Ni повышает вязкость
            base_kcv += Mn * 5   # Mn умеренно повышает
            base_kcv -= C * 200  # C сильно снижает
            base_kcv -= Si * 20  # Si снижает
            base_kcv -= P * 5000  # P очень вреден

            base_kcv = max(10, min(300, base_kcv))

            # Конвертация в Дж (KV = KCV × площадь)
            impact_energy = base_kcv * STANDARD_SPECIMEN_AREA

        kcv = impact_energy / STANDARD_SPECIMEN_AREA

        return ImpactProperties(
            impact_energy_j=round(max(5, impact_energy), 1),
            kcv_j_cm2=round(max(5, kcv), 1),
            transition_temp_c=round(transition_temp, 0),
            upper_shelf_energy_j=round(impact_energy * 1.3, 1),
            lower_shelf_energy_j=round(impact_energy * 0.1, 1),
            ductile_fraction_percent=80.0 if transition_temp < 0 else 50.0,
        )

    # =========================================================================
    # КОРРОЗИОННЫЕ СВОЙСТВА
    # =========================================================================

    def predict_corrosion(self, composition: Dict[str, float]) -> CorrosionProperties:
        """
        Прогноз коррозионных свойств.

        Формулы:
        - PREN = Cr + 3.3×Mo + 16×N (индекс питтинговой стойкости)
        - CPT ≈ 2.5 × PREN - 30 (критическая температура питтинга)

        Args:
            composition: Химический состав

        Returns:
            CorrosionProperties с количественными характеристиками коррозии
        """
        Cr = composition.get("Cr", 0)
        Mo = composition.get("Mo", 0)
        N = composition.get("N", 0)
        Ni = composition.get("Ni", 0)
        C = composition.get("C", 0)

        # PREN - всегда рассчитывается по формуле
        pren = Cr + 3.3 * Mo + 16 * N

        # ML прогноз скорости коррозии
        corrosion_rate = None
        if "corrosion_rate" in self.models:
            try:
                X = self._prepare_ml_features(composition)
                X_scaled = self.scalers["corrosion_rate"].transform(X)
                corrosion_rate = float(self.models["corrosion_rate"].predict(X_scaled)[0])
            except Exception as e:
                logger.warning(f"Ошибка ML прогноза corrosion_rate: {e}")

        # Эмпирический расчёт скорости коррозии
        if corrosion_rate is None:
            if Cr >= 12 and C < 0.1:
                # Нержавеющая сталь
                corrosion_rate = 0.01  # мм/год
            elif Cr >= 10:
                corrosion_rate = 0.05
            elif Cr >= 5:
                corrosion_rate = 0.1
            else:
                # Углеродистая сталь
                corrosion_rate = 0.5 - Cr * 0.03 - Ni * 0.02

            corrosion_rate = max(0.001, corrosion_rate)

        # Критическая температура питтинга
        cpt = 2.5 * pren - 30 if pren > 20 else None

        return CorrosionProperties(
            pren=round(pren, 1),
            cpt_c=round(cpt, 0) if cpt else None,
            corrosion_rate_mm_year=round(corrosion_rate, 4),
            passivation_potential_v=0.2 if Cr > 12 else None,
            pitting_potential_v=0.3 + pren * 0.01 if pren > 20 else None,
        )

    # =========================================================================
    # ТЕРМООБРАБОТКА
    # =========================================================================

    def predict_heat_treatment(
        self, composition: Dict[str, float]
    ) -> HeatTreatmentProperties:
        """
        Прогноз свойств термообработки.

        Эмпирические формулы (Andrews, 1965):
        - Ac1 = 727 - 10.7×Mn - 16.9×Ni + 29.1×Si + 16.9×Cr + 6.38×W
        - Ac3 = 910 - 203×√C - 15.2×Ni + 44.7×Si + 104×V + 31.5×Mo
        - Ms = 539 - 423×C - 30.4×Mn - 17.7×Ni - 12.1×Cr - 7.5×Mo

        Углеродный эквивалент (IIW):
        CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15

        Args:
            composition: Химический состав

        Returns:
            HeatTreatmentProperties с критическими температурами
        """
        C = composition.get("C", 0)
        Mn = composition.get("Mn", 0)
        Si = composition.get("Si", 0)
        Cr = composition.get("Cr", 0)
        Ni = composition.get("Ni", 0)
        Mo = composition.get("Mo", 0)
        V = composition.get("V", 0)
        W = composition.get("W", 0)
        Cu = composition.get("Cu", 0)

        # Углеродный эквивалент (IIW)
        ce = C + Mn / 6 + (Cr + Mo + V) / 5 + (Ni + Cu) / 15

        # ML прогноз или эмпирические формулы
        ac1 = ac3 = ms = quench_hrc = None

        # Попытка ML прогноза
        for prop in ["ac1_temp", "ac3_temp", "ms_temp", "quench_hardness"]:
            if prop in self.models:
                try:
                    X = self._prepare_ml_features(composition)
                    X_scaled = self.scalers[prop].transform(X)
                    val = float(self.models[prop].predict(X_scaled)[0])
                    if prop == "ac1_temp":
                        ac1 = val
                    elif prop == "ac3_temp":
                        ac3 = val
                    elif prop == "ms_temp":
                        ms = val
                    elif prop == "quench_hardness":
                        quench_hrc = val
                except Exception as e:
                    logger.warning(f"Ошибка ML прогноза {prop}: {e}")

        # Эмпирические формулы Andrews (1965)
        if ac1 is None:
            ac1 = 727 - 10.7 * Mn - 16.9 * Ni + 29.1 * Si + 16.9 * Cr + 6.38 * W

        if ac3 is None:
            ac3 = 910 - 203 * math.sqrt(max(0, C)) - 15.2 * Ni + 44.7 * Si + 104 * V + 31.5 * Mo

        if ms is None:
            ms = 539 - 423 * C - 30.4 * Mn - 17.7 * Ni - 12.1 * Cr - 7.5 * Mo

        # Твёрдость после закалки (формула Юста)
        if quench_hrc is None and C > 0.1:
            quench_hrc = 20 + 60 * math.sqrt(C)
            quench_hrc = min(67, quench_hrc)  # Максимум HRC

        # Mf температура (примерно Ms - 200°C)
        mf = ms - 200 if ms > 200 else None

        # Рекомендуемые температуры
        quench_temp = ac3 + 50 if ac3 else None
        temper_temp = 200 + C * 100  # Базовая рекомендация

        return HeatTreatmentProperties(
            carbon_equivalent=round(ce, 3),
            ac1_temp_c=round(ac1, 0),
            ac3_temp_c=round(ac3, 0),
            ms_temp_c=round(ms, 0),
            mf_temp_c=round(mf, 0) if mf else None,
            quench_hardness_hrc=round(quench_hrc, 1) if quench_hrc else None,
            hardenability_mm=10 + Cr * 2 + Mo * 5 + Mn * 1,  # Оценка
            recommended_quench_temp_c=round(quench_temp, 0) if quench_temp else None,
            recommended_temper_temp_c=round(temper_temp, 0),
        )

    # =========================================================================
    # ИЗНОСОСТОЙКОСТЬ
    # =========================================================================

    def predict_wear(
        self, composition: Dict[str, float], hardness_hv: float
    ) -> WearProperties:
        """
        Прогноз износостойкости.

        Эмпирические формулы:
        - Wear_index ∝ (HV/200)^1.5 × (1 + V_carbide × 0.02)
        - V_carbide = C×15 + Cr×0.3 + Mo×1 + V×3 + W×0.5

        Args:
            composition: Химический состав
            hardness_hv: Твёрдость по Виккерсу

        Returns:
            WearProperties с характеристиками износостойкости
        """
        C = composition.get("C", 0)
        Cr = composition.get("Cr", 0)
        Mo = composition.get("Mo", 0)
        V = composition.get("V", 0)
        W = composition.get("W", 0)

        # ML прогноз
        wear_index = None
        if "wear_index" in self.models:
            try:
                X = self._prepare_ml_features(composition)
                X_scaled = self.scalers["wear_index"].transform(X)
                wear_index = float(self.models["wear_index"].predict(X_scaled)[0])
            except Exception as e:
                logger.warning(f"Ошибка ML прогноза wear_index: {e}")

        # Объём карбидной фазы (%)
        carbide_volume = C * 15 + Cr * 0.3 + Mo * 1 + V * 3 + W * 0.5
        carbide_volume = min(40, max(0, carbide_volume))

        # Эмпирический расчёт индекса износа
        if wear_index is None:
            # Базовый индекс от твёрдости
            wear_index = (hardness_hv / 200) ** 1.5

            # Влияние карбидов
            wear_index *= (1 + carbide_volume * 0.02)

            # Нормализация к диапазону 0-10
            wear_index = min(10, wear_index)

        # Потеря массы (обратно пропорциональна износостойкости)
        mass_loss = 100 / (wear_index + 1)  # мг при стандартном тесте

        # Класс износостойкости
        if wear_index > 5:
            abrasion_class = "very_high"
        elif wear_index > 3:
            abrasion_class = "high"
        elif wear_index > 1.5:
            abrasion_class = "medium"
        else:
            abrasion_class = "low"

        return WearProperties(
            wear_resistance_index=round(wear_index, 2),
            mass_loss_mg=round(mass_loss, 1),
            volume_loss_mm3=round(mass_loss / 7.85, 2),  # Для плотности стали
            carbide_volume_percent=round(carbide_volume, 1),
            abrasion_resistance_class=abrasion_class,
        )

    # =========================================================================
    # ПОЛНЫЙ ПРОГНОЗ
    # =========================================================================

    def predict_full(self, composition: AlloyComposition) -> FullPredictionResponse:
        """
        Выполнить полный прогноз всех свойств сплава.

        Прогнозирует все доступные свойства:
        - Механические (прочность, твёрдость, удлинение)
        - Усталостные (предел выносливости)
        - Ударная вязкость (KCV, переходная температура)
        - Коррозионные (PREN, скорость коррозии)
        - Термообработка (критические температуры)
        - Износостойкость (индекс износа)

        Args:
            composition: Химический состав

        Returns:
            FullPredictionResponse со всеми свойствами
        """
        comp_dict = composition.model_dump()
        physical_features = calculate_physical_features(comp_dict)

        warnings = []
        models_used = []

        # Проверка суммы
        total = composition.total_percent()
        if abs(total - 100) > 5:
            warnings.append(f"Сумма компонентов ({total:.1f}%) отличается от 100%")

        # 1. Механические свойства
        if self.models and self.scalers:
            mechanical = self._predict_with_ml(comp_dict)
            confidence = 0.85
            models_used.extend(["yield_strength", "tensile_strength", "elongation", "hardness"])
        else:
            mechanical, confidence = self._estimate_properties_by_rules(comp_dict)
            warnings.append("Механические: эмпирические формулы")

        # 2. Усталостные свойства
        fatigue = self.predict_fatigue(comp_dict, mechanical.tensile_strength_mpa)
        if "fatigue" in self.loaded_categories:
            models_used.append("fatigue_limit")
        else:
            warnings.append("Усталость: эмпирические формулы")

        # 3. Ударная вязкость
        impact = self.predict_impact(comp_dict)
        if "impact" in self.loaded_categories:
            models_used.extend(["impact_energy", "transition_temp"])
        else:
            warnings.append("Ударная вязкость: формула Пикеринга")

        # 4. Коррозионные свойства
        corrosion = self.predict_corrosion(comp_dict)
        if "corrosion" in self.loaded_categories:
            models_used.extend(["pren", "corrosion_rate"])
        else:
            warnings.append("Коррозия: формула PREN")

        # 5. Термообработка
        heat_treatment = self.predict_heat_treatment(comp_dict)
        if "heat_treatment" in self.loaded_categories:
            models_used.extend(["ac1_temp", "ac3_temp", "ms_temp"])
        else:
            warnings.append("Термообработка: формулы Andrews")

        # 6. Износостойкость
        hardness_hv = mechanical.hardness_hv or 200
        wear = self.predict_wear(comp_dict, hardness_hv)
        if "wear" in self.loaded_categories:
            models_used.append("wear_index")
        else:
            warnings.append("Износ: эмпирические формулы")

        # Поведение и классификация
        behavior = self._predict_behavior(comp_dict, physical_features)
        classification = self._classify_alloy(comp_dict)

        return FullPredictionResponse(
            mechanical_properties=mechanical,
            fatigue_properties=fatigue,
            impact_properties=impact,
            corrosion_properties=corrosion,
            heat_treatment_properties=heat_treatment,
            wear_properties=wear,
            behavior=behavior,
            classification=classification,
            confidence=confidence,
            warnings=warnings,
            models_used=models_used,
        )


# Глобальный экземпляр предиктора
_predictor: Optional[AlloyPredictor] = None


def get_predictor() -> AlloyPredictor:
    """Получить экземпляр предиктора (singleton)."""
    global _predictor
    if _predictor is None:
        _predictor = AlloyPredictor()
    return _predictor
