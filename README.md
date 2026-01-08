# AlloyPredictor

![CI](https://github.com/Shchetnikovoff/auto_detect/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18-61dafb.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

AI-система для прогнозирования свойств металлических сплавов на основе их химического состава.

## Возможности

### Прогнозирование свойств
- **Механические свойства**
  - Предел прочности (UTS)
  - Предел текучести (YS)
  - Удлинение
  - Твёрдость (HRC/HV)
  - Модуль Юнга
  - Плотность

- **Усталостные свойства**
  - Предел усталости
  - Коэффициент усталости
  - Экспонента Basquin

- **Ударная вязкость**
  - Ударная работа (Дж)
  - KCV (Дж/см²)
  - Температура хрупко-вязкого перехода

- **Коррозионная стойкость**
  - PREN (Pitting Resistance Equivalent Number)
  - Скорость коррозии
  - Критическая температура питтинга

- **Параметры термообработки**
  - Углеродный эквивалент (CE)
  - Температуры Ac1, Ac3, Ms
  - Твёрдость после закалки
  - Прокаливаемость

- **Износостойкость**
  - Индекс износостойкости
  - Объём карбидов

### Оптимизация состава
Подбор оптимального химического состава под целевые свойства с использованием алгоритма дифференциальной эволюции.

### Справочник марок
База данных распространённых марок сталей с возможностью поиска и сравнения.

## Технологии

### Backend
- FastAPI 0.104
- scikit-learn (GradientBoostingRegressor)
- Pydantic v2
- Python 3.11

### Frontend
- React 18 + TypeScript
- Tailwind CSS
- Vite
- Recharts

### ML Модели (14 обученных моделей)
| Категория | Модели |
|-----------|--------|
| Механические | yield_strength, tensile_strength, elongation, hardness |
| Усталость | fatigue_limit |
| Удар | impact_energy, transition_temp |
| Коррозия | pren, corrosion_rate |
| Термообработка | ac1_temp, ac3_temp, ms_temp, quench_hardness |
| Износ | wear_index |

## Быстрый старт

### Запуск Backend

```bash
cd backend

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --reload
```

API будет доступен на http://localhost:8000
Документация Swagger: http://localhost:8000/docs

### Запуск Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на http://localhost:5173

### Docker

```bash
docker-compose up -d
```

## API Endpoints

### Прогнозирование

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/predict/` | Базовый прогноз механических свойств |
| POST | `/api/v1/predict/full` | Полный прогноз всех свойств |
| POST | `/api/v1/predict/fatigue` | Усталостные свойства |
| POST | `/api/v1/predict/impact` | Ударная вязкость |
| POST | `/api/v1/predict/corrosion` | Коррозионная стойкость |
| POST | `/api/v1/predict/heat-treatment` | Параметры термообработки |
| POST | `/api/v1/predict/wear` | Износостойкость |

### Оптимизация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/optimize/` | Оптимизация состава |

### Справочник

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/reference/grades` | Список марок сталей |

### Пример запроса

```bash
curl -X POST http://localhost:8000/api/v1/predict/full \
  -H "Content-Type: application/json" \
  -d '{"Fe": 97.5, "C": 0.45, "Si": 0.25, "Mn": 0.65}'
```

## Поддерживаемые элементы

Fe, C, Si, Mn, Cr, Ni, Mo, V, W, Co, Ti, Al, Cu, Nb, P, S, N

## Тестирование

### Backend

```bash
cd backend
pytest tests/ -v
```

### Линтинг

```bash
cd backend
ruff check app/
```

## Структура проекта

```
alloy-predictor/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API эндпоинты
│   │   ├── ml/              # ML модели и предикторы
│   │   ├── schemas/         # Pydantic схемы
│   │   └── main.py          # Точка входа FastAPI
│   ├── tests/               # Pytest тесты
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # API клиент
│   │   ├── pages/           # React страницы
│   │   └── App.tsx
│   └── package.json
├── datasets_for_review/     # Датасеты для обучения
├── docker-compose.yml
└── README.md
```

## Источники данных

- MPEA Database (1,545 сплавов)
- Синтетические данные на основе эмпирических формул (3,000 сплавов)
- Дополнительные датасеты: fatigue, impact, corrosion, heat_treatment, wear

## Лицензия

MIT
