"""
Генерация датасетов для прогнозирования свойств сплавов.
Основано на эмпирических формулах из научной литературы.

Источники:
1. ASM Handbook, Vol. 1: Properties and Selection: Irons, Steels, and High-Performance Alloys
2. Smithells Metals Reference Book, 8th Edition
3. NIMS Fatigue Data Sheets
4. ISO 3183 / API 5L standards for pipeline steels
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

OUTPUT_DIR = Path(__file__).parent


def generate_fatigue_dataset(n_samples=2000):
    """
    Генерация датасета усталостной прочности.

    Формулы:
    - Предел выносливости σ_-1 ≈ 0.4-0.5 × σ_в (для сталей)
    - Уравнение Басквина: Δσ/2 = σ'_f × (2N_f)^b
    - Коэффициент b ≈ -0.05 to -0.12 для сталей

    Источник: ASTM E466, NIMS Fatigue Data Sheets
    """
    data = []

    for _ in range(n_samples):
        # Химический состав
        C = np.random.uniform(0.05, 1.2)
        Si = np.random.uniform(0.1, 1.5)
        Mn = np.random.uniform(0.3, 2.0)
        Cr = np.random.uniform(0, 18)
        Ni = np.random.uniform(0, 12)
        Mo = np.random.uniform(0, 3)
        V = np.random.uniform(0, 0.5)

        Fe = 100 - C - Si - Mn - Cr - Ni - Mo - V
        if Fe < 50:
            continue

        # Предел прочности (эмпирическая формула)
        tensile_strength = (400 + C * 1000 + Mn * 40 + Cr * 25 +
                          Ni * 20 + Mo * 50 + V * 120 + Si * 100)
        tensile_strength += np.random.normal(0, 30)

        # Предел выносливости (формула для сталей)
        # σ_-1 ≈ k × σ_в, где k = 0.4-0.5
        k = 0.45 + np.random.uniform(-0.05, 0.05)
        fatigue_limit = k * tensile_strength

        # Коэффициент Басквина
        basquin_b = -0.085 + np.random.uniform(-0.03, 0.03)

        # Число циклов до разрушения при σ_a = 0.7 × σ_-1
        sigma_a = 0.7 * fatigue_limit
        sigma_f = 1.75 * tensile_strength  # коэффициент усталостной прочности
        N_f = (sigma_a / sigma_f) ** (1 / basquin_b) / 2
        N_f = max(1e4, min(1e8, N_f))

        # Влияние легирующих на усталость
        # Cr и Mo улучшают усталостную прочность
        fatigue_improvement = 1 + Cr * 0.01 + Mo * 0.02 + V * 0.05
        fatigue_limit *= fatigue_improvement

        data.append({
            'Fe': round(Fe, 2),
            'C': round(C, 3),
            'Si': round(Si, 2),
            'Mn': round(Mn, 2),
            'Cr': round(Cr, 2),
            'Ni': round(Ni, 2),
            'Mo': round(Mo, 2),
            'V': round(V, 3),
            'tensile_strength_MPa': round(tensile_strength, 1),
            'fatigue_limit_MPa': round(fatigue_limit, 1),
            'fatigue_ratio': round(fatigue_limit / tensile_strength, 3),
            'basquin_exponent': round(basquin_b, 4),
            'cycles_to_failure_1e6': round(np.log10(N_f), 2),
            'test_type': np.random.choice(['rotating_bending', 'axial', 'torsion']),
            'R_ratio': np.random.choice([-1, 0, 0.1]),
        })

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / 'fatigue_properties.csv', index=False)
    print(f"Fatigue dataset: {len(df)} samples")
    return df


def generate_impact_toughness_dataset(n_samples=1500):
    """
    Генерация датасета ударной вязкости.

    Формулы:
    - KCV (Дж/см²) зависит от C, Mn, Ni и температуры
    - Переходная температура T_tr
    - Формула Пикеринга для T_tr

    Источник: ASTM E23, ISO 148-1
    """
    data = []

    for _ in range(n_samples):
        C = np.random.uniform(0.05, 0.8)
        Si = np.random.uniform(0.1, 1.0)
        Mn = np.random.uniform(0.3, 2.0)
        Cr = np.random.uniform(0, 5)
        Ni = np.random.uniform(0, 5)
        Mo = np.random.uniform(0, 1)
        P = np.random.uniform(0.005, 0.035)
        S = np.random.uniform(0.005, 0.03)

        Fe = 100 - C - Si - Mn - Cr - Ni - Mo - P - S
        if Fe < 85:
            continue

        # Температура испытания
        test_temp = np.random.choice([-40, -20, 0, 20, 100])

        # Базовая ударная вязкость при 20°C
        # Формула на основе эмпирических данных
        base_kcv = 150 - C * 200 - P * 3000 - S * 2000 + Ni * 10 + Mn * 5
        base_kcv = max(10, base_kcv)

        # Влияние температуры (S-образная кривая)
        # Переходная температура по формуле Пикеринга
        T_tr = -19 + 44 * Si + 700 * np.sqrt(P) + 2.2 * (100 * C) ** 0.5 - 11.5 * np.sqrt(Ni)

        # Корректировка KCV по температуре
        temp_factor = 1 / (1 + np.exp(-(test_temp - T_tr) / 15))
        kcv = base_kcv * temp_factor + np.random.normal(0, 10)
        kcv = max(5, min(300, kcv))

        # Процент вязкой составляющей
        ductile_fraction = temp_factor * 100

        data.append({
            'Fe': round(Fe, 2),
            'C': round(C, 3),
            'Si': round(Si, 2),
            'Mn': round(Mn, 2),
            'Cr': round(Cr, 2),
            'Ni': round(Ni, 2),
            'Mo': round(Mo, 2),
            'P': round(P, 4),
            'S': round(S, 4),
            'test_temperature_C': test_temp,
            'impact_energy_J': round(kcv * 0.8, 1),  # KCV в Дж (площадь ~0.8 см²)
            'KCV_J_cm2': round(kcv, 1),
            'transition_temp_C': round(T_tr, 1),
            'ductile_fraction_percent': round(ductile_fraction, 1),
            'specimen_type': 'Charpy_V',
        })

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / 'impact_toughness.csv', index=False)
    print(f"Impact toughness dataset: {len(df)} samples")
    return df


def generate_corrosion_dataset(n_samples=1500):
    """
    Генерация датасета коррозионной стойкости.

    Формулы:
    - PREN (Pitting Resistance Equivalent Number) = Cr + 3.3×Mo + 16×N
    - PRE_N = Cr + 3.3×Mo + 16×N (для нержавеющих сталей)
    - Скорость коррозии зависит от среды и состава

    Источник: ASTM G48, ISO 17864
    """
    data = []

    for _ in range(n_samples):
        # Генерируем разные типы сталей
        steel_type = np.random.choice(['carbon', 'low_alloy', 'stainless', 'duplex'])

        if steel_type == 'carbon':
            C = np.random.uniform(0.1, 0.5)
            Cr = np.random.uniform(0, 0.5)
            Ni = np.random.uniform(0, 0.5)
            Mo = 0
            N = 0
        elif steel_type == 'low_alloy':
            C = np.random.uniform(0.1, 0.4)
            Cr = np.random.uniform(0.5, 5)
            Ni = np.random.uniform(0, 3)
            Mo = np.random.uniform(0, 1)
            N = 0
        elif steel_type == 'stainless':
            C = np.random.uniform(0.02, 0.15)
            Cr = np.random.uniform(12, 20)
            Ni = np.random.uniform(6, 14)
            Mo = np.random.uniform(0, 3)
            N = np.random.uniform(0, 0.2)
        else:  # duplex
            C = np.random.uniform(0.02, 0.05)
            Cr = np.random.uniform(20, 27)
            Ni = np.random.uniform(4, 8)
            Mo = np.random.uniform(2, 4)
            N = np.random.uniform(0.1, 0.3)

        Si = np.random.uniform(0.2, 1.0)
        Mn = np.random.uniform(0.5, 2.0)

        Fe = 100 - C - Si - Mn - Cr - Ni - Mo - N

        # PREN (Pitting Resistance Equivalent Number)
        PREN = Cr + 3.3 * Mo + 16 * N

        # Критическая температура питтингообразования (CPT)
        # CPT ≈ 2.5 × PREN - 30 (приблизительная формула)
        CPT = 2.5 * PREN - 30 + np.random.normal(0, 5)
        CPT = max(-20, min(100, CPT))

        # Скорость коррозии в морской воде (мм/год)
        if Cr >= 12:
            corrosion_rate = 0.001 + np.random.exponential(0.01)
        elif Cr >= 5:
            corrosion_rate = 0.05 + np.random.exponential(0.05)
        else:
            corrosion_rate = 0.1 + np.random.exponential(0.2)

        # Классификация коррозионной стойкости
        if PREN > 40:
            corrosion_class = 'excellent'
        elif PREN > 30:
            corrosion_class = 'very_good'
        elif PREN > 20:
            corrosion_class = 'good'
        elif Cr > 10:
            corrosion_class = 'moderate'
        else:
            corrosion_class = 'low'

        data.append({
            'Fe': round(Fe, 2),
            'C': round(C, 3),
            'Si': round(Si, 2),
            'Mn': round(Mn, 2),
            'Cr': round(Cr, 2),
            'Ni': round(Ni, 2),
            'Mo': round(Mo, 2),
            'N': round(N, 3),
            'steel_type': steel_type,
            'PREN': round(PREN, 1),
            'CPT_C': round(CPT, 1),
            'corrosion_rate_mm_year': round(corrosion_rate, 4),
            'corrosion_resistance': corrosion_class,
            'environment': np.random.choice(['seawater', 'industrial', 'atmospheric', 'acidic']),
        })

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / 'corrosion_resistance.csv', index=False)
    print(f"Corrosion dataset: {len(df)} samples")
    return df


def generate_heat_treatment_dataset(n_samples=2000):
    """
    Генерация датасета термообработки.

    Формулы:
    - Углеродный эквивалент CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15
    - Критическая скорость охлаждения
    - Твёрдость после закалки (формула Юста)

    Источник: ASM Handbook Vol. 4, ISO 4957
    """
    data = []

    for _ in range(n_samples):
        C = np.random.uniform(0.1, 1.2)
        Si = np.random.uniform(0.1, 2.0)
        Mn = np.random.uniform(0.3, 2.0)
        Cr = np.random.uniform(0, 15)
        Ni = np.random.uniform(0, 8)
        Mo = np.random.uniform(0, 3)
        V = np.random.uniform(0, 1)
        W = np.random.uniform(0, 5)
        Cu = np.random.uniform(0, 0.5)

        Fe = 100 - C - Si - Mn - Cr - Ni - Mo - V - W - Cu
        if Fe < 60:
            continue

        # Углеродный эквивалент (формула IIW)
        CE_IIW = C + Mn/6 + (Cr + Mo + V)/5 + (Ni + Cu)/15

        # Углеродный эквивалент (формула Pcm для низкоуглеродистых)
        Pcm = C + Si/30 + (Mn + Cu + Cr)/20 + Ni/60 + Mo/15 + V/10

        # Температуры превращений
        Ac1 = 727 - 10.7*Mn - 16.9*Ni + 29.1*Si + 16.9*Cr + 6.38*W
        Ac3 = 910 - 203*np.sqrt(C) - 15.2*Ni + 44.7*Si + 104*V + 31.5*Mo
        Ms = 539 - 423*C - 30.4*Mn - 17.7*Ni - 12.1*Cr - 7.5*Mo

        # Тип термообработки
        treatment = np.random.choice(['quenching', 'normalizing', 'annealing', 'tempering'])

        if treatment == 'quenching':
            # Твёрдость после закалки (формула Юста)
            HRC_max = 20 + 60*np.sqrt(C)
            HRC = min(67, HRC_max) + np.random.normal(0, 2)
            cooling_medium = np.random.choice(['water', 'oil', 'air'])
        elif treatment == 'normalizing':
            HRC = 15 + 30*C + np.random.normal(0, 3)
            cooling_medium = 'air'
        elif treatment == 'annealing':
            HRC = 10 + 20*C + np.random.normal(0, 2)
            cooling_medium = 'furnace'
        else:  # tempering
            tempering_temp = np.random.uniform(150, 650)
            # Снижение твёрдости при отпуске
            HRC = (20 + 60*np.sqrt(C)) * (1 - tempering_temp/1000) + np.random.normal(0, 2)
            cooling_medium = 'air'

        HRC = max(10, min(68, HRC))

        # Прокаливаемость (условный диаметр)
        D_crit = 5 + 20*C + 10*Mn + 5*Cr + 30*Mo + 4*Ni

        data.append({
            'Fe': round(Fe, 2),
            'C': round(C, 3),
            'Si': round(Si, 2),
            'Mn': round(Mn, 2),
            'Cr': round(Cr, 2),
            'Ni': round(Ni, 2),
            'Mo': round(Mo, 2),
            'V': round(V, 3),
            'W': round(W, 2),
            'Cu': round(Cu, 2),
            'CE_IIW': round(CE_IIW, 3),
            'Pcm': round(Pcm, 3),
            'Ac1_C': round(Ac1, 0),
            'Ac3_C': round(Ac3, 0),
            'Ms_C': round(Ms, 0),
            'treatment_type': treatment,
            'cooling_medium': cooling_medium,
            'hardness_HRC': round(HRC, 1),
            'hardenability_mm': round(D_crit, 1),
            'weldability': 'good' if CE_IIW < 0.4 else ('fair' if CE_IIW < 0.5 else 'poor'),
        })

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / 'heat_treatment.csv', index=False)
    print(f"Heat treatment dataset: {len(df)} samples")
    return df


def generate_wear_resistance_dataset(n_samples=1000):
    """
    Генерация датасета износостойкости.

    Формулы:
    - Износостойкость ~ HV^n (n ≈ 1-2)
    - Влияние карбидов (Cr, V, W, Mo)

    Источник: ASTM G65, ISO 9352
    """
    data = []

    for _ in range(n_samples):
        C = np.random.uniform(0.2, 2.0)
        Si = np.random.uniform(0.1, 1.5)
        Mn = np.random.uniform(0.3, 1.5)
        Cr = np.random.uniform(0, 20)
        Mo = np.random.uniform(0, 5)
        V = np.random.uniform(0, 3)
        W = np.random.uniform(0, 10)

        Fe = 100 - C - Si - Mn - Cr - Mo - V - W
        if Fe < 50:
            continue

        # Твёрдость
        HV = 200 + C * 300 + Cr * 10 + Mo * 20 + V * 50 + W * 15
        HV += np.random.normal(0, 30)
        HV = max(150, min(900, HV))

        # Объём карбидов (%)
        carbide_volume = C * 15 + Cr * 0.3 + Mo * 1 + V * 3 + W * 0.5
        carbide_volume = min(40, carbide_volume)

        # Износостойкость (относительная, больше = лучше)
        # Зависит от твёрдости и карбидов
        wear_resistance = (HV / 200) ** 1.5 * (1 + carbide_volume * 0.02)
        wear_resistance += np.random.normal(0, 0.2)

        # Потеря массы (г) при стандартном тесте ASTM G65
        mass_loss = 1.0 / wear_resistance + np.random.exponential(0.05)
        mass_loss = max(0.01, min(2.0, mass_loss))

        data.append({
            'Fe': round(Fe, 2),
            'C': round(C, 3),
            'Si': round(Si, 2),
            'Mn': round(Mn, 2),
            'Cr': round(Cr, 2),
            'Mo': round(Mo, 2),
            'V': round(V, 2),
            'W': round(W, 2),
            'hardness_HV': round(HV, 0),
            'carbide_volume_percent': round(carbide_volume, 1),
            'wear_resistance_index': round(wear_resistance, 2),
            'mass_loss_g': round(mass_loss, 3),
            'test_method': 'ASTM_G65',
            'abrasive_type': np.random.choice(['sand', 'alumina', 'SiC']),
        })

    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_DIR / 'wear_resistance.csv', index=False)
    print(f"Wear resistance dataset: {len(df)} samples")
    return df


if __name__ == '__main__':
    print("Generating datasets based on empirical formulas...\n")

    generate_fatigue_dataset()
    generate_impact_toughness_dataset()
    generate_corrosion_dataset()
    generate_heat_treatment_dataset()
    generate_wear_resistance_dataset()

    print("\nAll datasets generated successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
