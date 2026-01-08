# Датасеты для проекта AlloyPredictor

## Обзор датасетов

| Датасет | Записей | Свойства | Источник |
|---------|---------|----------|----------|
| MPEA Dataset | 1,545 | YS, UTS, HV, Elongation | Nature Scientific Data (открытый) |
| Fatigue Properties | 2,000 | Предел выносливости, циклы до разрушения | Эмпирические формулы |
| Impact Toughness | 1,500 | KCV, переходная температура | Эмпирические формулы |
| Corrosion Resistance | 1,500 | PREN, CPT, скорость коррозии | Эмпирические формулы |
| Heat Treatment | 2,000 | CE, Ac1, Ac3, Ms, твёрдость после ТО | Эмпирические формулы |
| Wear Resistance | 1,000 | Износостойкость, потеря массы | Эмпирические формулы |
| **ИТОГО** | **9,545** | | |

---

## 1. MPEA Dataset (Multi-Principal Element Alloys)

**Файл:** `mpea_dataset.csv`

### Источник (ОТКРЫТЫЙ)
- **Публикация:** Nature Scientific Data (2020)
- **DOI:** https://doi.org/10.1038/s41597-020-00768-9
- **GitHub:** https://github.com/CitrineInformatics/MPEA_dataset
- **Лицензия:** CC BY 4.0

### Описание
Датасет высокоэнтропийных сплавов (HEA), собранный из 571 научной публикации.

| Свойство | Записей | Диапазон |
|----------|---------|----------|
| Yield Strength (YS) | 1,067 | 24 - 3,416 МПа |
| Tensile Strength (UTS) | 539 | 80 - 4,024 МПа |
| Elongation | 619 | 0 - 105% |
| Hardness (HV) | 530 | 95 - 1,183 |

---

## 2. Fatigue Properties (Усталостная прочность)

**Файл:** `fatigue_properties.csv`

### Эмпирические формулы

**Предел выносливости:**
```
σ_-1 ≈ k × σ_в, где k = 0.40-0.50 (для сталей)
```

**Уравнение Басквина:**
```
Δσ/2 = σ'_f × (2N_f)^b
b ≈ -0.05 to -0.12 для сталей
```

### Источники формул
- ASTM E466 - Standard Practice for Conducting Force Controlled Constant Amplitude Axial Fatigue Tests
- NIMS Fatigue Data Sheets
- Bannantine, J.A. "Fundamentals of Metal Fatigue Analysis"

### Колонки
| Колонка | Описание |
|---------|----------|
| Fe, C, Si, Mn, Cr, Ni, Mo, V | Химический состав (%) |
| tensile_strength_MPa | Предел прочности |
| fatigue_limit_MPa | Предел выносливости |
| fatigue_ratio | σ_-1 / σ_в |
| basquin_exponent | Показатель уравнения Басквина |
| cycles_to_failure_1e6 | log₁₀(N_f) |
| test_type | Тип испытания |
| R_ratio | Коэффициент асимметрии цикла |

---

## 3. Impact Toughness (Ударная вязкость)

**Файл:** `impact_toughness.csv`

### Эмпирические формулы

**Переходная температура (формула Пикеринга):**
```
T_tr = -19 + 44×Si + 700×√P + 2.2×√(100×C) - 11.5×√Ni
```

**Ударная вязкость KCV:**
```
KCV(T) = KCV_max × [1 / (1 + exp(-(T - T_tr) / 15))]
```

### Источники формул
- ASTM E23 - Standard Test Methods for Notched Bar Impact Testing
- ISO 148-1 - Metallic materials — Charpy pendulum impact test
- Pickering, F.B. "Physical Metallurgy and the Design of Steels"

### Колонки
| Колонка | Описание |
|---------|----------|
| test_temperature_C | Температура испытания |
| impact_energy_J | Ударная вязкость (Дж) |
| KCV_J_cm2 | KCV (Дж/см²) |
| transition_temp_C | Переходная температура |
| ductile_fraction_percent | Доля вязкой составляющей |

---

## 4. Corrosion Resistance (Коррозионная стойкость)

**Файл:** `corrosion_resistance.csv`

### Эмпирические формулы

**PREN (Pitting Resistance Equivalent Number):**
```
PREN = Cr + 3.3×Mo + 16×N
```

**Критическая температура питтингообразования:**
```
CPT ≈ 2.5 × PREN - 30 (°C)
```

### Источники формул
- ASTM G48 - Standard Test Methods for Pitting and Crevice Corrosion Resistance
- ISO 17864 - Corrosion of metals and alloys
- Sedriks, A.J. "Corrosion of Stainless Steels"

### Колонки
| Колонка | Описание |
|---------|----------|
| steel_type | Тип стали (carbon, stainless, duplex) |
| PREN | Индекс питтинговой стойкости |
| CPT_C | Критическая температура питтинга |
| corrosion_rate_mm_year | Скорость коррозии |
| corrosion_resistance | Класс коррозионной стойкости |

---

## 5. Heat Treatment (Термообработка)

**Файл:** `heat_treatment.csv`

### Эмпирические формулы

**Углеродный эквивалент (IIW):**
```
CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15
```

**Температуры превращений:**
```
Ac1 = 727 - 10.7×Mn - 16.9×Ni + 29.1×Si + 16.9×Cr + 6.38×W
Ac3 = 910 - 203×√C - 15.2×Ni + 44.7×Si + 104×V + 31.5×Mo
Ms = 539 - 423×C - 30.4×Mn - 17.7×Ni - 12.1×Cr - 7.5×Mo
```

**Твёрдость после закалки (формула Юста):**
```
HRC_max ≈ 20 + 60×√C
```

### Источники формул
- ASM Handbook, Vol. 4: Heat Treating
- ISO 4957 - Tool steels
- Andrews, K.W. "Empirical Formulae for the Calculation of Transformation Temperatures"

### Колонки
| Колонка | Описание |
|---------|----------|
| CE_IIW | Углеродный эквивалент (IIW) |
| Pcm | Углеродный эквивалент (Pcm) |
| Ac1_C, Ac3_C | Критические температуры |
| Ms_C | Температура начала мартенситного превращения |
| treatment_type | Вид термообработки |
| hardness_HRC | Твёрдость после ТО |
| hardenability_mm | Прокаливаемость |
| weldability | Свариваемость |

---

## 6. Wear Resistance (Износостойкость)

**Файл:** `wear_resistance.csv`

### Эмпирические формулы

**Износостойкость:**
```
Wear_index ∝ (HV/200)^1.5 × (1 + V_carbide × 0.02)
```

**Объём карбидов:**
```
V_carbide = C×15 + Cr×0.3 + Mo×1 + V×3 + W×0.5
```

### Источники формул
- ASTM G65 - Standard Test Method for Measuring Abrasion Using the Dry Sand/Rubber Wheel Apparatus
- ISO 9352 - Plastics — Determination of resistance to wear by abrasive wheels
- Zum Gahr, K.H. "Microstructure and Wear of Materials"

### Колонки
| Колонка | Описание |
|---------|----------|
| hardness_HV | Твёрдость по Виккерсу |
| carbide_volume_percent | Объём карбидной фазы |
| wear_resistance_index | Индекс износостойкости |
| mass_loss_g | Потеря массы при испытании |

---

## Использование в проекте

### Скрипт генерации
```bash
python generate_datasets.py
```

### Интеграция с ML
```python
import pandas as pd

# Загрузка всех датасетов
mpea = pd.read_csv('mpea_dataset.csv')
fatigue = pd.read_csv('fatigue_properties.csv')
impact = pd.read_csv('impact_toughness.csv')
corrosion = pd.read_csv('corrosion_resistance.csv')
heat = pd.read_csv('heat_treatment.csv')
wear = pd.read_csv('wear_resistance.csv')

print(f"Total samples: {len(mpea) + len(fatigue) + len(impact) + len(corrosion) + len(heat) + len(wear)}")
```

---

## Ссылки на источники

### Открытые датасеты
1. [MPEA Dataset - Nature Scientific Data](https://www.nature.com/articles/s41597-020-00768-9)
2. [CitrineInformatics GitHub](https://github.com/CitrineInformatics/MPEA_dataset)
3. [Materials Informatics Resources](https://github.com/sedaoturak/data-resources-for-materials-science)

### Справочники
1. ASM Handbook, Vol. 1: Properties and Selection: Irons, Steels
2. ASM Handbook, Vol. 4: Heat Treating
3. Smithells Metals Reference Book, 8th Edition
4. NIMS Fatigue Data Sheets

### Стандарты
- ASTM E23 (Impact Testing)
- ASTM E466 (Fatigue Testing)
- ASTM G48 (Corrosion Testing)
- ASTM G65 (Wear Testing)
- ISO 148-1, ISO 17864, ISO 4957, ISO 9352
