"""Feature engineering для сплавов - физико-химические признаки."""

import numpy as np
from typing import Dict, List

# Атомные массы элементов
ATOMIC_MASSES = {
    "Fe": 55.845, "C": 12.011, "Si": 28.086, "Mn": 54.938,
    "Cr": 51.996, "Ni": 58.693, "Mo": 95.94, "V": 50.942,
    "W": 183.84, "Co": 58.933, "Ti": 47.867, "Al": 26.982,
    "Cu": 63.546, "Nb": 92.906, "P": 30.974, "S": 32.065, "N": 14.007
}

# Атомные радиусы (пм)
ATOMIC_RADII = {
    "Fe": 126, "C": 77, "Si": 111, "Mn": 127,
    "Cr": 128, "Ni": 124, "Mo": 139, "V": 134,
    "W": 139, "Co": 125, "Ti": 147, "Al": 143,
    "Cu": 128, "Nb": 146, "P": 107, "S": 105, "N": 56
}

# Электроотрицательность по Полингу
ELECTRONEGATIVITY = {
    "Fe": 1.83, "C": 2.55, "Si": 1.90, "Mn": 1.55,
    "Cr": 1.66, "Ni": 1.91, "Mo": 2.16, "V": 1.63,
    "W": 2.36, "Co": 1.88, "Ti": 1.54, "Al": 1.61,
    "Cu": 1.90, "Nb": 1.60, "P": 2.19, "S": 2.58, "N": 3.04
}

# Модули упругости (ГПа)
YOUNGS_MODULUS = {
    "Fe": 211, "C": 1050, "Si": 130, "Mn": 198,
    "Cr": 279, "Ni": 200, "Mo": 329, "V": 128,
    "W": 411, "Co": 209, "Ti": 116, "Al": 70,
    "Cu": 130, "Nb": 105, "P": 11, "S": 12, "N": None
}

# Температуры плавления (°C)
MELTING_POINTS = {
    "Fe": 1538, "C": 3550, "Si": 1414, "Mn": 1246,
    "Cr": 1907, "Ni": 1455, "Mo": 2623, "V": 1910,
    "W": 3422, "Co": 1495, "Ti": 1668, "Al": 660,
    "Cu": 1085, "Nb": 2477, "P": 44, "S": 115, "N": -210
}


def calculate_physical_features(composition: Dict[str, float]) -> Dict[str, float]:
    """
    Рассчитать физико-химические признаки на основе состава.

    Args:
        composition: Словарь {элемент: процент}

    Returns:
        Словарь с рассчитанными признаками
    """
    features = {}

    # Нормализация состава (исключаем нулевые элементы)
    total = sum(composition.values())
    if total == 0:
        total = 1

    # Атомные доли
    atomic_fractions = {}
    total_atoms = 0
    for elem, pct in composition.items():
        if pct > 0 and elem in ATOMIC_MASSES:
            atoms = pct / ATOMIC_MASSES[elem]
            atomic_fractions[elem] = atoms
            total_atoms += atoms

    if total_atoms > 0:
        for elem in atomic_fractions:
            atomic_fractions[elem] /= total_atoms

    # Средний атомный радиус
    avg_radius = 0
    for elem, frac in atomic_fractions.items():
        if elem in ATOMIC_RADII:
            avg_radius += frac * ATOMIC_RADII[elem]
    features["avg_atomic_radius"] = avg_radius

    # Разброс атомных радиусов (параметр δ)
    if avg_radius > 0:
        delta = 0
        for elem, frac in atomic_fractions.items():
            if elem in ATOMIC_RADII:
                delta += frac * ((1 - ATOMIC_RADII[elem] / avg_radius) ** 2)
        features["atomic_radius_delta"] = np.sqrt(delta) * 100
    else:
        features["atomic_radius_delta"] = 0

    # Средняя электроотрицательность
    avg_en = 0
    for elem, frac in atomic_fractions.items():
        if elem in ELECTRONEGATIVITY:
            avg_en += frac * ELECTRONEGATIVITY[elem]
    features["avg_electronegativity"] = avg_en

    # Разброс электроотрицательности
    if avg_en > 0:
        delta_en = 0
        for elem, frac in atomic_fractions.items():
            if elem in ELECTRONEGATIVITY:
                delta_en += frac * ((ELECTRONEGATIVITY[elem] - avg_en) ** 2)
        features["electronegativity_delta"] = np.sqrt(delta_en)
    else:
        features["electronegativity_delta"] = 0

    # Параметр VEC (Valence Electron Concentration)
    # Упрощённая модель: считаем по группе в периодической таблице
    VEC_VALUES = {
        "Fe": 8, "C": 4, "Si": 4, "Mn": 7,
        "Cr": 6, "Ni": 10, "Mo": 6, "V": 5,
        "W": 6, "Co": 9, "Ti": 4, "Al": 3,
        "Cu": 11, "Nb": 5, "P": 5, "S": 6, "N": 5
    }
    vec = 0
    for elem, frac in atomic_fractions.items():
        if elem in VEC_VALUES:
            vec += frac * VEC_VALUES[elem]
    features["vec"] = vec

    # Средняя температура плавления
    avg_tm = 0
    for elem, frac in atomic_fractions.items():
        if elem in MELTING_POINTS and MELTING_POINTS[elem] is not None:
            avg_tm += frac * MELTING_POINTS[elem]
    features["avg_melting_point"] = avg_tm

    # Углеродный эквивалент (CE) для сталей
    # CE = C + Mn/6 + (Cr + Mo + V)/5 + (Ni + Cu)/15
    ce = composition.get("C", 0)
    ce += composition.get("Mn", 0) / 6
    ce += (composition.get("Cr", 0) + composition.get("Mo", 0) + composition.get("V", 0)) / 5
    ce += (composition.get("Ni", 0) + composition.get("Cu", 0)) / 15
    features["carbon_equivalent"] = ce

    # Хромовый эквивалент (для нержавеющих сталей)
    # Cr_eq = Cr + Mo + 1.5*Si + 0.5*Nb
    cr_eq = composition.get("Cr", 0)
    cr_eq += composition.get("Mo", 0)
    cr_eq += 1.5 * composition.get("Si", 0)
    cr_eq += 0.5 * composition.get("Nb", 0)
    features["chromium_equivalent"] = cr_eq

    # Никелевый эквивалент
    # Ni_eq = Ni + 30*C + 0.5*Mn
    ni_eq = composition.get("Ni", 0)
    ni_eq += 30 * composition.get("C", 0)
    ni_eq += 0.5 * composition.get("Mn", 0)
    features["nickel_equivalent"] = ni_eq

    # Конфигурационная энтропия (для многокомпонентных сплавов)
    # S_conf = -R * Σ(x_i * ln(x_i))
    R = 8.314  # Дж/(моль·К)
    entropy = 0
    for elem, frac in atomic_fractions.items():
        if frac > 0:
            entropy -= frac * np.log(frac)
    features["config_entropy"] = entropy * R

    # Количество значимых элементов (>1%)
    significant_elements = sum(1 for pct in composition.values() if pct > 1)
    features["num_significant_elements"] = significant_elements

    # Является ли это HEA (High Entropy Alloy)
    # Критерий: 5+ элементов с долями 5-35%
    hea_elements = sum(1 for pct in composition.values() if 5 <= pct <= 35)
    features["is_hea"] = 1 if hea_elements >= 5 else 0

    return features


def get_all_features(composition: Dict[str, float]) -> List[float]:
    """
    Получить полный вектор признаков для ML модели.

    Args:
        composition: Словарь {элемент: процент}

    Returns:
        Список признаков
    """
    # Базовые признаки (сырой состав)
    elements = ["Fe", "C", "Si", "Mn", "Cr", "Ni", "Mo", "V",
                "W", "Co", "Ti", "Al", "Cu", "Nb", "P", "S", "N"]
    base_features = [composition.get(elem, 0) for elem in elements]

    # Физические признаки
    physical = calculate_physical_features(composition)
    physical_features = [
        physical["avg_atomic_radius"],
        physical["atomic_radius_delta"],
        physical["avg_electronegativity"],
        physical["electronegativity_delta"],
        physical["vec"],
        physical["avg_melting_point"],
        physical["carbon_equivalent"],
        physical["chromium_equivalent"],
        physical["nickel_equivalent"],
        physical["config_entropy"],
        physical["num_significant_elements"],
        physical["is_hea"]
    ]

    return base_features + physical_features


def get_feature_names() -> List[str]:
    """Получить названия всех признаков."""
    base_names = ["Fe", "C", "Si", "Mn", "Cr", "Ni", "Mo", "V",
                  "W", "Co", "Ti", "Al", "Cu", "Nb", "P", "S", "N"]

    physical_names = [
        "avg_atomic_radius",
        "atomic_radius_delta",
        "avg_electronegativity",
        "electronegativity_delta",
        "vec",
        "avg_melting_point",
        "carbon_equivalent",
        "chromium_equivalent",
        "nickel_equivalent",
        "config_entropy",
        "num_significant_elements",
        "is_hea"
    ]

    return base_names + physical_names
