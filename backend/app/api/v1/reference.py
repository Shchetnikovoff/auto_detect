"""API эндпоинты для справочника марок сталей."""

from fastapi import APIRouter, Query
from typing import List, Optional

router = APIRouter()

# База данных распространённых марок сталей
STEEL_GRADES = [
    {
        "grade": "Ст3",
        "standard": "ГОСТ",
        "composition": {"Fe": 98.5, "C": 0.18, "Si": 0.17, "Mn": 0.50},
        "yield_strength": 245,
        "tensile_strength": 380,
        "applications": ["строительные конструкции", "листовой прокат"],
        "type": "углеродистая"
    },
    {
        "grade": "45",
        "standard": "ГОСТ",
        "composition": {"Fe": 97.5, "C": 0.45, "Si": 0.25, "Mn": 0.65},
        "yield_strength": 360,
        "tensile_strength": 610,
        "applications": ["валы", "шестерни", "крепёж"],
        "type": "углеродистая"
    },
    {
        "grade": "40Х",
        "standard": "ГОСТ",
        "composition": {"Fe": 96.8, "C": 0.40, "Si": 0.25, "Mn": 0.65, "Cr": 1.0},
        "yield_strength": 785,
        "tensile_strength": 980,
        "applications": ["валы", "оси", "шестерни высоконагруженные"],
        "type": "легированная"
    },
    {
        "grade": "40ХН",
        "standard": "ГОСТ",
        "composition": {"Fe": 95.5, "C": 0.40, "Si": 0.25, "Mn": 0.60, "Cr": 0.7, "Ni": 1.5},
        "yield_strength": 835,
        "tensile_strength": 1030,
        "applications": ["валы", "шатуны", "болты ответственные"],
        "type": "легированная"
    },
    {
        "grade": "12Х18Н10Т",
        "standard": "ГОСТ",
        "composition": {"Fe": 68.0, "C": 0.12, "Si": 0.8, "Mn": 2.0, "Cr": 18.0, "Ni": 10.0, "Ti": 0.8},
        "yield_strength": 200,
        "tensile_strength": 510,
        "applications": ["пищевое оборудование", "химическая промышленность"],
        "type": "нержавеющая аустенитная"
    },
    {
        "grade": "AISI 304",
        "standard": "AISI",
        "composition": {"Fe": 69.0, "C": 0.08, "Si": 0.75, "Mn": 2.0, "Cr": 19.0, "Ni": 9.0},
        "yield_strength": 215,
        "tensile_strength": 505,
        "applications": ["кухонное оборудование", "архитектура"],
        "type": "stainless austenitic"
    },
    {
        "grade": "AISI 316",
        "standard": "AISI",
        "composition": {"Fe": 65.0, "C": 0.08, "Si": 0.75, "Mn": 2.0, "Cr": 17.0, "Ni": 12.0, "Mo": 2.5},
        "yield_strength": 205,
        "tensile_strength": 515,
        "applications": ["медицина", "морское оборудование", "химическая промышленность"],
        "type": "stainless austenitic"
    },
    {
        "grade": "AISI 4140",
        "standard": "AISI",
        "composition": {"Fe": 96.8, "C": 0.40, "Si": 0.25, "Mn": 0.85, "Cr": 0.95, "Mo": 0.20},
        "yield_strength": 655,
        "tensile_strength": 1020,
        "applications": ["валы", "шестерни", "болты"],
        "type": "low alloy"
    },
    {
        "grade": "Р6М5",
        "standard": "ГОСТ",
        "composition": {"Fe": 80.0, "C": 0.85, "Si": 0.4, "Mn": 0.4, "Cr": 4.0, "Mo": 5.0, "W": 6.0, "V": 2.0},
        "yield_strength": None,
        "tensile_strength": None,
        "applications": ["режущий инструмент", "свёрла", "фрезы"],
        "type": "быстрорежущая"
    },
    {
        "grade": "ШХ15",
        "standard": "ГОСТ",
        "composition": {"Fe": 96.0, "C": 1.0, "Si": 0.25, "Mn": 0.35, "Cr": 1.5},
        "yield_strength": None,
        "tensile_strength": None,
        "applications": ["подшипники", "ролики"],
        "type": "подшипниковая"
    },
    {
        "grade": "09Г2С",
        "standard": "ГОСТ",
        "composition": {"Fe": 97.0, "C": 0.12, "Si": 0.7, "Mn": 1.5},
        "yield_strength": 345,
        "tensile_strength": 490,
        "applications": ["сварные конструкции", "трубопроводы", "мосты"],
        "type": "низколегированная"
    },
    {
        "grade": "65Г",
        "standard": "ГОСТ",
        "composition": {"Fe": 97.5, "C": 0.65, "Si": 0.25, "Mn": 1.0},
        "yield_strength": 430,
        "tensile_strength": 750,
        "applications": ["пружины", "рессоры", "ножи"],
        "type": "рессорно-пружинная"
    },
]


@router.get("/grades", response_model=List[dict])
async def get_steel_grades(
    type_filter: Optional[str] = Query(None, description="Фильтр по типу стали"),
    min_strength: Optional[int] = Query(None, description="Минимальный предел прочности"),
    search: Optional[str] = Query(None, description="Поиск по марке или применению"),
) -> List[dict]:
    """
    Получить справочник марок сталей.

    Параметры:
    - type_filter: Фильтр по типу (углеродистая, легированная, нержавеющая, etc.)
    - min_strength: Минимальный предел прочности (МПа)
    - search: Поиск по названию марки или области применения
    """
    results = STEEL_GRADES.copy()

    # Фильтрация по типу
    if type_filter:
        results = [g for g in results if type_filter.lower() in g["type"].lower()]

    # Фильтрация по прочности
    if min_strength:
        results = [g for g in results if g["tensile_strength"] and g["tensile_strength"] >= min_strength]

    # Поиск
    if search:
        search_lower = search.lower()
        results = [
            g for g in results
            if search_lower in g["grade"].lower() or
               any(search_lower in app.lower() for app in g["applications"])
        ]

    return results


@router.get("/grades/{grade}", response_model=dict)
async def get_grade_details(grade: str) -> dict:
    """Получить детальную информацию о марке стали."""
    for g in STEEL_GRADES:
        if g["grade"].lower() == grade.lower():
            return g

    return {"error": f"Марка '{grade}' не найдена", "available": [g["grade"] for g in STEEL_GRADES]}


@router.get("/types")
async def get_steel_types() -> List[str]:
    """Получить список типов сталей."""
    types = set(g["type"] for g in STEEL_GRADES)
    return sorted(types)
