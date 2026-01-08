"""
Скрипт обучения ML моделей для прогнозирования свойств сплавов.

Обучаемые модели:
1. Механические свойства (MPEA + синтетические данные):
   - yield_strength (предел текучести)
   - tensile_strength (предел прочности)
   - elongation (удлинение)
   - hardness (твёрдость)

2. Усталостная прочность (fatigue_properties.csv):
   - fatigue_limit (предел выносливости)

3. Ударная вязкость (impact_toughness.csv):
   - impact_energy (ударная вязкость)
   - transition_temp (переходная температура)

4. Коррозионная стойкость (corrosion_resistance.csv):
   - pren (Pitting Resistance Equivalent Number)
   - corrosion_rate (скорость коррозии)

5. Термообработка (heat_treatment.csv):
   - ac1_temp (температура Ac1)
   - ac3_temp (температура Ac3)
   - ms_temp (температура начала мартенситного превращения)
   - quench_hardness (твёрдость после закалки)

6. Износостойкость (wear_resistance.csv):
   - wear_index (индекс износостойкости)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from pathlib import Path
import requests
import re
import logging
from typing import Dict, List, Tuple, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Директории
MODELS_DIR = Path(__file__).parent / "models"
DATA_DIR = Path(__file__).parent.parent / "data" / "datasets"
REVIEW_DIR = Path(__file__).parent.parent.parent.parent / "datasets_for_review"

MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# ЧАСТЬ 1: ЗАГРУЗКА ДАННЫХ
# ============================================================================

def download_mpea_dataset() -> Path:
    """Скачать MPEA датасет с GitHub."""
    url = "https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/master/MPEA_dataset.csv"
    filepath = DATA_DIR / "mpea_dataset.csv"

    if filepath.exists():
        logger.info(f"MPEA dataset already exists at {filepath}")
        return filepath

    logger.info(f"Downloading MPEA dataset from {url}")
    response = requests.get(url)
    response.raise_for_status()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(response.text)

    logger.info(f"Saved to {filepath}")
    return filepath


def load_additional_datasets() -> Dict[str, pd.DataFrame]:
    """
    Загрузка дополнительных датасетов из datasets_for_review.

    Возвращает словарь с датасетами:
    - fatigue: усталостная прочность
    - impact: ударная вязкость
    - corrosion: коррозионная стойкость
    - heat_treatment: термообработка
    - wear: износостойкость
    """
    datasets = {}

    # Пути к файлам
    files = {
        "fatigue": "fatigue_properties.csv",
        "impact": "impact_toughness.csv",
        "corrosion": "corrosion_resistance.csv",
        "heat_treatment": "heat_treatment.csv",
        "wear": "wear_resistance.csv",
    }

    for name, filename in files.items():
        filepath = REVIEW_DIR / filename
        if filepath.exists():
            try:
                df = pd.read_csv(filepath)
                datasets[name] = df
                logger.info(f"Loaded {name}: {len(df)} samples from {filepath}")
            except Exception as e:
                logger.warning(f"Could not load {name}: {e}")
        else:
            logger.warning(f"File not found: {filepath}")

    return datasets


# ============================================================================
# ЧАСТЬ 2: ПАРСИНГ И ПОДГОТОВКА ДАННЫХ
# ============================================================================

def parse_formula(formula: str) -> dict:
    """
    Парсинг формулы сплава в словарь элементов.

    Примеры:
    - "CoCrFeNi" -> {"Co": 25, "Cr": 25, "Fe": 25, "Ni": 25}
    - "Al0.5CoCrFeNi" -> {"Al": 10, "Co": 22.5, "Cr": 22.5, "Fe": 22.5, "Ni": 22.5}
    """
    if pd.isna(formula) or not formula:
        return {}

    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, str(formula))

    elements = {}
    total = 0

    for elem, amount in matches:
        if elem:
            amt = float(amount) if amount else 1.0
            elements[elem] = amt
            total += amt

    # Нормализация до 100%
    if total > 0:
        for elem in elements:
            elements[elem] = (elements[elem] / total) * 100

    return elements


def generate_synthetic_steel_data(n_samples: int = 2000) -> pd.DataFrame:
    """
    Генерация синтетических данных для обычных сталей.
    Основано на эмпирических формулах металловедения.
    """
    np.random.seed(42)
    data = []

    for _ in range(n_samples):
        # Генерация случайного состава
        C = np.random.uniform(0.05, 1.5)
        Si = np.random.uniform(0.1, 1.0)
        Mn = np.random.uniform(0.3, 2.0)
        Cr = np.random.choice([0, np.random.uniform(0.5, 18)], p=[0.5, 0.5])
        Ni = np.random.choice([0, np.random.uniform(0.5, 12)], p=[0.6, 0.4])
        Mo = np.random.choice([0, np.random.uniform(0.1, 3)], p=[0.7, 0.3])
        V = np.random.choice([0, np.random.uniform(0.05, 0.5)], p=[0.8, 0.2])

        Fe = 100 - C - Si - Mn - Cr - Ni - Mo - V
        if Fe < 50:
            continue

        # Эмпирические формулы для механических свойств
        YS = 250 + C * 800 + Mn * 30 + Cr * 20 + Ni * 15 + Mo * 40 + V * 100 + Si * 80
        YS += np.random.normal(0, 30)

        UTS = 400 + C * 1000 + Mn * 40 + Cr * 25 + Ni * 20 + Mo * 50 + V * 120 + Si * 100
        UTS += np.random.normal(0, 40)

        EL = max(5, 30 - C * 25 - Si * 5 - Mn * 2 - Cr * 1 + Ni * 0.5)
        EL += np.random.normal(0, 2)
        EL = max(3, min(50, EL))

        HV = 100 + C * 300 + Cr * 10 + Mo * 20 + V * 50
        HV += np.random.normal(0, 15)

        data.append({
            "Fe": Fe, "C": C, "Si": Si, "Mn": Mn,
            "Cr": Cr, "Ni": Ni, "Mo": Mo, "V": V,
            "YS": max(150, YS),
            "UTS": max(300, UTS),
            "Elongation": EL,
            "HV": max(80, HV)
        })

    return pd.DataFrame(data)


def load_and_prepare_mpea_data(filepath: Path) -> pd.DataFrame:
    """Загрузка и подготовка MPEA датасета."""
    df = pd.read_csv(filepath)

    col_map = {
        "FORMULA": "formula",
        "PROPERTY: YS (MPa)": "YS",
        "PROPERTY: UTS (MPa)": "UTS",
        "PROPERTY: Elongation (%)": "Elongation",
        "PROPERTY: HV": "HV",
    }

    df = df.rename(columns=col_map)
    compositions = df["formula"].apply(parse_formula)

    elements = ["Fe", "C", "Si", "Mn", "Cr", "Ni", "Mo", "V", "W", "Co", "Ti", "Al", "Cu", "Nb"]
    for elem in elements:
        df[elem] = compositions.apply(lambda x: x.get(elem, 0))

    df["YS"] = pd.to_numeric(df["YS"], errors="coerce")
    df["UTS"] = pd.to_numeric(df["UTS"], errors="coerce")
    df["Elongation"] = pd.to_numeric(df["Elongation"], errors="coerce")
    df["HV"] = pd.to_numeric(df["HV"], errors="coerce")

    return df


# ============================================================================
# ЧАСТЬ 3: ПОДГОТОВКА ПРИЗНАКОВ
# ============================================================================

def prepare_features(df: pd.DataFrame, feature_type: str = "mechanical") -> Tuple[pd.DataFrame, List[str]]:
    """
    Подготовка признаков для обучения.

    Args:
        df: DataFrame с данными
        feature_type: Тип признаков:
            - "mechanical": для механических свойств
            - "fatigue": для усталостной прочности
            - "impact": для ударной вязкости
            - "corrosion": для коррозионной стойкости
            - "heat_treatment": для термообработки
            - "wear": для износостойкости
    """
    df = df.copy()

    # Базовые элементы (присутствуют во всех датасетах)
    base_elements = ["Fe", "C", "Si", "Mn", "Cr", "Ni", "Mo", "V"]
    feature_cols = [col for col in base_elements if col in df.columns]

    # Заполняем отсутствующие элементы нулями
    for elem in base_elements:
        if elem not in df.columns:
            df[elem] = 0

    # Добавляем инженерные признаки в зависимости от типа
    if feature_type == "mechanical":
        # Углеродный эквивалент
        df["CE"] = df["C"] + df["Mn"] / 6 + (df["Cr"] + df["Mo"] + df.get("V", 0)) / 5
        feature_cols.append("CE")

        # Сумма легирующих
        df["total_alloy"] = df["Cr"] + df["Ni"] + df["Mo"] + df.get("V", 0)
        feature_cols.append("total_alloy")

    elif feature_type == "fatigue":
        # Для усталости важны: прочность, структура
        df["CE"] = df["C"] + df["Mn"] / 6 + (df["Cr"] + df["Mo"] + df.get("V", 0)) / 5
        feature_cols.append("CE")

        if "tensile_strength_MPa" in df.columns:
            feature_cols.append("tensile_strength_MPa")

    elif feature_type == "impact":
        # Для ударной вязкости важны: примеси, структура
        df["CE"] = df["C"] + df["Mn"] / 6 + (df["Cr"] + df["Mo"] + df.get("V", 0)) / 5
        feature_cols.append("CE")

        # Переходная температура зависит от примесей (P, S)
        if "P" in df.columns:
            feature_cols.append("P")
        if "S" in df.columns:
            feature_cols.append("S")

        if "test_temperature_C" in df.columns:
            feature_cols.append("test_temperature_C")

    elif feature_type == "corrosion":
        # Для коррозии: хром, молибден, азот
        if "N" in df.columns:
            feature_cols.append("N")

    elif feature_type == "heat_treatment":
        # Для термообработки: углеродный эквивалент, все легирующие
        df["CE_IIW"] = df["C"] + df["Mn"] / 6 + (df["Cr"] + df["Mo"] + df.get("V", 0)) / 5 + (df["Ni"] + df.get("Cu", 0)) / 15
        feature_cols.append("CE_IIW")

        if "W" in df.columns:
            feature_cols.append("W")

    elif feature_type == "wear":
        # Для износостойкости: твёрдость, карбиды
        if "hardness_HV" in df.columns:
            feature_cols.append("hardness_HV")
        if "carbide_volume_percent" in df.columns:
            feature_cols.append("carbide_volume_percent")

    # Убираем дубликаты и проверяем наличие колонок
    feature_cols = list(dict.fromkeys(feature_cols))
    feature_cols = [col for col in feature_cols if col in df.columns]

    X = df[feature_cols].fillna(0)
    return X, feature_cols


# ============================================================================
# ЧАСТЬ 4: ОБУЧЕНИЕ МОДЕЛЕЙ
# ============================================================================

def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_name: str,
    model_type: str = "gradient_boosting"
) -> Tuple[Optional[object], Optional[object], Optional[Dict]]:
    """
    Обучение модели.

    Args:
        X: Матрица признаков
        y: Целевая переменная
        model_name: Название модели для логирования
        model_type: Тип модели ("gradient_boosting" или "random_forest")

    Returns:
        (model, scaler, metrics) или (None, None, None) если недостаточно данных
    """
    # Удаление NaN
    mask = ~y.isna()
    X_clean = X[mask]
    y_clean = y[mask]

    if len(y_clean) < 30:
        logger.warning(f"Not enough data for {model_name}: {len(y_clean)} samples (need 30+)")
        return None, None, None

    # Разделение на train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X_clean, y_clean, test_size=0.2, random_state=42
    )

    # Масштабирование
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Выбор модели
    if model_type == "random_forest":
        model = RandomForestRegressor(
            n_estimators=150,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
    else:
        model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )

    model.fit(X_train_scaled, y_train)

    # Оценка
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Кросс-валидация для более надёжной оценки
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
    cv_r2_mean = cv_scores.mean()
    cv_r2_std = cv_scores.std()

    logger.info(f"{model_name}: MAE={mae:.2f}, R2={r2:.3f}, CV_R2={cv_r2_mean:.3f}+/-{cv_r2_std:.3f}, samples={len(y_clean)}")

    return model, scaler, {
        "mae": mae,
        "r2": r2,
        "cv_r2_mean": cv_r2_mean,
        "cv_r2_std": cv_r2_std,
        "samples": len(y_clean)
    }


def save_model(model, scaler, model_name: str, feature_names: List[str], metrics: Dict):
    """Сохранение модели, скейлера и метаданных."""
    model_path = MODELS_DIR / f"{model_name}_model.pkl"
    scaler_path = MODELS_DIR / f"{model_name}_scaler.pkl"

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    # Сохраняем метаданные для каждой модели отдельно
    meta_path = MODELS_DIR / f"{model_name}_meta.pkl"
    joblib.dump({
        "feature_names": feature_names,
        "metrics": metrics
    }, meta_path)

    logger.info(f"Saved: {model_path}")


# ============================================================================
# ЧАСТЬ 5: ОБУЧЕНИЕ ВСЕХ МОДЕЛЕЙ
# ============================================================================

def train_mechanical_models(combined_df: pd.DataFrame) -> Dict:
    """Обучение моделей для механических свойств."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING MECHANICAL PROPERTY MODELS")
    logger.info("=" * 60)

    X, feature_names = prepare_features(combined_df, "mechanical")
    logger.info(f"Features: {feature_names}")

    targets = {
        "yield_strength": "YS",
        "tensile_strength": "UTS",
        "elongation": "Elongation",
        "hardness": "HV"
    }

    results = {}

    for model_name, target_col in targets.items():
        logger.info(f"\nTraining {model_name}...")
        y = combined_df[target_col]
        model, scaler, metrics = train_model(X, y, model_name)

        if model is not None:
            save_model(model, scaler, model_name, feature_names, metrics)
            results[model_name] = metrics

    return results


def train_fatigue_models(df: pd.DataFrame) -> Dict:
    """Обучение моделей для усталостной прочности."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING FATIGUE MODELS")
    logger.info("=" * 60)

    X, feature_names = prepare_features(df, "fatigue")
    logger.info(f"Features: {feature_names}")

    results = {}

    # Предел выносливости
    if "fatigue_limit_MPa" in df.columns:
        logger.info("\nTraining fatigue_limit...")
        y = df["fatigue_limit_MPa"]
        model, scaler, metrics = train_model(X, y, "fatigue_limit")

        if model is not None:
            save_model(model, scaler, "fatigue_limit", feature_names, metrics)
            results["fatigue_limit"] = metrics

    return results


def train_impact_models(df: pd.DataFrame) -> Dict:
    """Обучение моделей для ударной вязкости."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING IMPACT TOUGHNESS MODELS")
    logger.info("=" * 60)

    X, feature_names = prepare_features(df, "impact")
    logger.info(f"Features: {feature_names}")

    results = {}

    # Ударная вязкость
    if "impact_energy_J" in df.columns:
        logger.info("\nTraining impact_energy...")
        y = df["impact_energy_J"]
        model, scaler, metrics = train_model(X, y, "impact_energy")

        if model is not None:
            save_model(model, scaler, "impact_energy", feature_names, metrics)
            results["impact_energy"] = metrics

    # Переходная температура
    if "transition_temp_C" in df.columns:
        logger.info("\nTraining transition_temp...")
        y = df["transition_temp_C"]
        model, scaler, metrics = train_model(X, y, "transition_temp")

        if model is not None:
            save_model(model, scaler, "transition_temp", feature_names, metrics)
            results["transition_temp"] = metrics

    return results


def train_corrosion_models(df: pd.DataFrame) -> Dict:
    """Обучение моделей для коррозионной стойкости."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING CORROSION RESISTANCE MODELS")
    logger.info("=" * 60)

    X, feature_names = prepare_features(df, "corrosion")
    logger.info(f"Features: {feature_names}")

    results = {}

    # PREN
    if "PREN" in df.columns:
        logger.info("\nTraining pren...")
        y = df["PREN"]
        model, scaler, metrics = train_model(X, y, "pren")

        if model is not None:
            save_model(model, scaler, "pren", feature_names, metrics)
            results["pren"] = metrics

    # Скорость коррозии
    if "corrosion_rate_mm_year" in df.columns:
        logger.info("\nTraining corrosion_rate...")
        y = df["corrosion_rate_mm_year"]
        model, scaler, metrics = train_model(X, y, "corrosion_rate")

        if model is not None:
            save_model(model, scaler, "corrosion_rate", feature_names, metrics)
            results["corrosion_rate"] = metrics

    return results


def train_heat_treatment_models(df: pd.DataFrame) -> Dict:
    """Обучение моделей для параметров термообработки."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING HEAT TREATMENT MODELS")
    logger.info("=" * 60)

    X, feature_names = prepare_features(df, "heat_treatment")
    logger.info(f"Features: {feature_names}")

    results = {}

    targets = {
        "ac1_temp": "Ac1_C",
        "ac3_temp": "Ac3_C",
        "ms_temp": "Ms_C",
        "quench_hardness": "hardness_HRC"
    }

    for model_name, target_col in targets.items():
        if target_col in df.columns:
            logger.info(f"\nTraining {model_name}...")
            y = df[target_col]
            model, scaler, metrics = train_model(X, y, model_name)

            if model is not None:
                save_model(model, scaler, model_name, feature_names, metrics)
                results[model_name] = metrics

    return results


def train_wear_models(df: pd.DataFrame) -> Dict:
    """Обучение моделей для износостойкости."""
    logger.info("\n" + "=" * 60)
    logger.info("TRAINING WEAR RESISTANCE MODELS")
    logger.info("=" * 60)

    X, feature_names = prepare_features(df, "wear")
    logger.info(f"Features: {feature_names}")

    results = {}

    # Индекс износостойкости
    if "wear_resistance_index" in df.columns:
        logger.info("\nTraining wear_index...")
        y = df["wear_resistance_index"]
        model, scaler, metrics = train_model(X, y, "wear_index")

        if model is not None:
            save_model(model, scaler, "wear_index", feature_names, metrics)
            results["wear_index"] = metrics

    return results


# ============================================================================
# ЧАСТЬ 6: ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Основная функция обучения всех моделей."""
    logger.info("=" * 70)
    logger.info("AlloyPredictor - Extended ML Training Pipeline")
    logger.info("=" * 70)

    all_results = {}

    # -------------------------------------------------------------------------
    # 1. МЕХАНИЧЕСКИЕ СВОЙСТВА (MPEA + синтетические данные)
    # -------------------------------------------------------------------------
    logger.info("\n[1/6] Loading data for mechanical properties...")

    try:
        mpea_path = download_mpea_dataset()
        mpea_df = load_and_prepare_mpea_data(mpea_path)
        logger.info(f"MPEA dataset: {len(mpea_df)} samples")
    except Exception as e:
        logger.warning(f"Could not load MPEA dataset: {e}")
        mpea_df = pd.DataFrame()

    synthetic_df = generate_synthetic_steel_data(3000)
    logger.info(f"Synthetic data: {len(synthetic_df)} samples")

    if len(mpea_df) > 0:
        common_cols = ["Fe", "C", "Si", "Mn", "Cr", "Ni", "Mo", "V", "YS", "UTS", "Elongation", "HV"]
        mpea_subset = mpea_df[common_cols].copy()
        combined_df = pd.concat([synthetic_df[common_cols], mpea_subset], ignore_index=True)
    else:
        combined_df = synthetic_df

    logger.info(f"Combined mechanical dataset: {len(combined_df)} samples")

    mechanical_results = train_mechanical_models(combined_df)
    all_results.update(mechanical_results)

    # -------------------------------------------------------------------------
    # 2. ДОПОЛНИТЕЛЬНЫЕ ДАТАСЕТЫ
    # -------------------------------------------------------------------------
    logger.info("\n[2/6] Loading additional datasets from datasets_for_review...")
    additional = load_additional_datasets()

    # -------------------------------------------------------------------------
    # 3. УСТАЛОСТНАЯ ПРОЧНОСТЬ
    # -------------------------------------------------------------------------
    if "fatigue" in additional:
        fatigue_results = train_fatigue_models(additional["fatigue"])
        all_results.update(fatigue_results)
    else:
        logger.warning("Fatigue dataset not found, skipping...")

    # -------------------------------------------------------------------------
    # 4. УДАРНАЯ ВЯЗКОСТЬ
    # -------------------------------------------------------------------------
    if "impact" in additional:
        impact_results = train_impact_models(additional["impact"])
        all_results.update(impact_results)
    else:
        logger.warning("Impact toughness dataset not found, skipping...")

    # -------------------------------------------------------------------------
    # 5. КОРРОЗИОННАЯ СТОЙКОСТЬ
    # -------------------------------------------------------------------------
    if "corrosion" in additional:
        corrosion_results = train_corrosion_models(additional["corrosion"])
        all_results.update(corrosion_results)
    else:
        logger.warning("Corrosion dataset not found, skipping...")

    # -------------------------------------------------------------------------
    # 6. ТЕРМООБРАБОТКА
    # -------------------------------------------------------------------------
    if "heat_treatment" in additional:
        heat_results = train_heat_treatment_models(additional["heat_treatment"])
        all_results.update(heat_results)
    else:
        logger.warning("Heat treatment dataset not found, skipping...")

    # -------------------------------------------------------------------------
    # 7. ИЗНОСОСТОЙКОСТЬ
    # -------------------------------------------------------------------------
    if "wear" in additional:
        wear_results = train_wear_models(additional["wear"])
        all_results.update(wear_results)
    else:
        logger.warning("Wear resistance dataset not found, skipping...")

    # -------------------------------------------------------------------------
    # СОХРАНЕНИЕ ОБЩИХ МЕТАДАННЫХ
    # -------------------------------------------------------------------------
    metadata = {
        "trained_models": list(all_results.keys()),
        "results": all_results,
        "datasets_used": {
            "mechanical": len(combined_df),
            "fatigue": len(additional.get("fatigue", [])),
            "impact": len(additional.get("impact", [])),
            "corrosion": len(additional.get("corrosion", [])),
            "heat_treatment": len(additional.get("heat_treatment", [])),
            "wear": len(additional.get("wear", [])),
        }
    }

    metadata_path = MODELS_DIR / "metadata.pkl"
    joblib.dump(metadata, metadata_path)

    # -------------------------------------------------------------------------
    # ИТОГОВЫЙ ОТЧЁТ
    # -------------------------------------------------------------------------
    logger.info("\n" + "=" * 70)
    logger.info("TRAINING COMPLETE!")
    logger.info("=" * 70)

    print("\n" + "=" * 60)
    print("MODEL PERFORMANCE SUMMARY")
    print("=" * 60)

    # Группировка по категориям
    categories = {
        "Mechanical Properties": ["yield_strength", "tensile_strength", "elongation", "hardness"],
        "Fatigue": ["fatigue_limit"],
        "Impact Toughness": ["impact_energy", "transition_temp"],
        "Corrosion": ["pren", "corrosion_rate"],
        "Heat Treatment": ["ac1_temp", "ac3_temp", "ms_temp", "quench_hardness"],
        "Wear Resistance": ["wear_index"],
    }

    for category, model_names in categories.items():
        category_models = {k: v for k, v in all_results.items() if k in model_names}
        if category_models:
            print(f"\n{category}:")
            print("-" * 40)
            for name, metrics in category_models.items():
                print(f"  {name}:")
                print(f"    MAE: {metrics['mae']:.2f}")
                print(f"    R2:  {metrics['r2']:.3f} (CV: {metrics['cv_r2_mean']:.3f})")
                print(f"    Samples: {metrics['samples']}")

    print("\n" + "=" * 60)
    print(f"Total models trained: {len(all_results)}")
    print(f"Models saved to: {MODELS_DIR}")
    print("=" * 60)

    return all_results


if __name__ == "__main__":
    main()
