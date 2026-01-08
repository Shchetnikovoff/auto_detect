"""
Оптимизатор состава сплава на основе дифференциальной эволюции.

Алгоритм оптимизации:
1. Определяем пространство поиска (границы для каждого элемента)
2. Задаём целевую функцию (fitness function), которая оценивает:
   - Соответствие целевым свойствам (прочность, твёрдость и т.д.)
   - Выполнение ограничений (запрещённые элементы, стоимость)
   - Сумма компонентов должна быть ~100%
3. Используем scipy.optimize.differential_evolution для поиска оптимума
4. Возвращаем лучшие решения с их прогнозируемыми свойствами

Метод differential_evolution выбран потому что:
- Не требует градиентов (наши ML модели - чёрные ящики)
- Хорошо работает с многомерными задачами
- Устойчив к локальным минимумам
- Можно легко добавлять ограничения
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from scipy.optimize import differential_evolution, OptimizeResult

logger = logging.getLogger(__name__)


# Стоимость элементов (относительная, $/кг)
# Используется для оптимизации по стоимости
ELEMENT_COSTS = {
    "Fe": 0.5,      # Железо - базовый, дешёвый
    "C": 0.1,       # Углерод - дешёвый
    "Si": 2.0,      # Кремний
    "Mn": 2.5,      # Марганец
    "Cr": 8.0,      # Хром - дорогой
    "Ni": 15.0,     # Никель - очень дорогой
    "Mo": 25.0,     # Молибден - дорогой
    "V": 30.0,      # Ванадий - дорогой
    "W": 35.0,      # Вольфрам - очень дорогой
    "Co": 50.0,     # Кобальт - самый дорогой
    "Ti": 20.0,     # Титан
    "Al": 3.0,      # Алюминий
    "Cu": 7.0,      # Медь
    "Nb": 40.0,     # Ниобий
    "P": 1.0,       # Фосфор (примесь)
    "S": 1.0,       # Сера (примесь)
    "N": 0.5,       # Азот
}

# Границы допустимых значений для каждого элемента (%)
ELEMENT_BOUNDS = {
    "Fe": (0, 100),
    "C": (0, 2.5),       # Выше 2.1% - уже чугун
    "Si": (0, 4.0),
    "Mn": (0, 15.0),
    "Cr": (0, 30.0),
    "Ni": (0, 35.0),
    "Mo": (0, 8.0),
    "V": (0, 3.0),
    "W": (0, 18.0),
    "Co": (0, 12.0),
    "Ti": (0, 3.0),
    "Al": (0, 10.0),     # Для сталей, не алюминиевых сплавов
    "Cu": (0, 4.0),
    "Nb": (0, 2.0),
    "N": (0, 0.5),
}

# Порядок элементов для вектора оптимизации
OPTIMIZATION_ELEMENTS = ["C", "Si", "Mn", "Cr", "Ni", "Mo", "V", "W", "Ti", "Al", "Cu"]


@dataclass
class OptimizationConfig:
    """Конфигурация оптимизатора."""

    # Целевые свойства (None = не оптимизировать)
    target_yield_strength: Optional[float] = None      # МПа
    target_tensile_strength: Optional[float] = None    # МПа
    target_elongation: Optional[float] = None          # %
    target_hardness: Optional[float] = None            # HRC

    # Ограничения
    base_element: str = "Fe"                           # Базовый элемент
    forbidden_elements: List[str] = None               # Запрещённые элементы
    max_cost_level: str = "high"                       # low/medium/high
    min_elements: Dict[str, float] = None              # Минимальные значения
    max_elements: Dict[str, float] = None              # Максимальные значения

    # Параметры алгоритма
    num_alternatives: int = 5                          # Количество альтернатив
    population_size: int = 50                          # Размер популяции
    max_iterations: int = 200                          # Максимум итераций
    tolerance: float = 1e-6                            # Точность сходимости

    def __post_init__(self):
        if self.forbidden_elements is None:
            self.forbidden_elements = []
        if self.min_elements is None:
            self.min_elements = {}
        if self.max_elements is None:
            self.max_elements = {}


class AlloyOptimizer:
    """
    Оптимизатор состава сплава.

    Использует дифференциальную эволюцию для поиска оптимального
    химического состава, который максимизирует соответствие
    целевым механическим свойствам при выполнении ограничений.
    """

    def __init__(self, predictor):
        """
        Инициализация оптимизатора.

        Args:
            predictor: Экземпляр AlloyPredictor для прогнозирования свойств
        """
        self.predictor = predictor
        self.config: Optional[OptimizationConfig] = None
        self._best_solutions: List[Tuple[Dict, float]] = []

    def _get_bounds(self) -> List[Tuple[float, float]]:
        """
        Получить границы для каждого оптимизируемого элемента.

        Учитывает:
        - Стандартные границы из ELEMENT_BOUNDS
        - Пользовательские min/max ограничения
        - Запрещённые элементы (границы = (0, 0))

        Returns:
            Список кортежей (min, max) для каждого элемента
        """
        bounds = []

        for elem in OPTIMIZATION_ELEMENTS:
            # Базовые границы
            low, high = ELEMENT_BOUNDS.get(elem, (0, 10))

            # Если элемент запрещён
            if elem in self.config.forbidden_elements:
                low, high = 0, 0
            else:
                # Пользовательские ограничения
                if elem in self.config.min_elements:
                    low = max(low, self.config.min_elements[elem])
                if elem in self.config.max_elements:
                    high = min(high, self.config.max_elements[elem])

            bounds.append((low, high))

        return bounds

    def _get_max_cost(self) -> float:
        """
        Получить максимально допустимую стоимость на основе уровня.

        Returns:
            Максимальная относительная стоимость сплава
        """
        cost_limits = {
            "low": 5.0,      # Только дешёвые элементы (Fe, C, Si, Mn)
            "medium": 15.0,  # Можно немного Cr, Ni
            "high": 50.0,    # Можно дорогие элементы
            "unlimited": float("inf")
        }
        return cost_limits.get(self.config.max_cost_level, 50.0)

    def _vector_to_composition(self, x: np.ndarray) -> Dict[str, float]:
        """
        Преобразовать вектор оптимизации в словарь состава.

        Args:
            x: Вектор значений элементов

        Returns:
            Словарь {element: percent}
        """
        composition = {}

        for i, elem in enumerate(OPTIMIZATION_ELEMENTS):
            if x[i] > 0.001:  # Игнорируем очень малые значения
                composition[elem] = round(x[i], 3)

        # Вычисляем Fe как остаток до 100%
        total_alloying = sum(composition.values())
        fe_content = max(0, 100 - total_alloying)

        if fe_content > 0.1:  # Если есть значимое количество Fe
            composition["Fe"] = round(fe_content, 2)

        return composition

    def _calculate_cost(self, composition: Dict[str, float]) -> float:
        """
        Рассчитать относительную стоимость состава.

        Args:
            composition: Словарь состава

        Returns:
            Относительная стоимость ($/кг)
        """
        total_cost = 0
        for elem, percent in composition.items():
            cost_per_kg = ELEMENT_COSTS.get(elem, 10.0)
            total_cost += (percent / 100) * cost_per_kg
        return total_cost

    def _fitness_function(self, x: np.ndarray) -> float:
        """
        Целевая функция для оптимизации (минимизируется).

        Чем меньше значение - тем лучше состав.

        Компоненты fitness:
        1. Отклонение от целевых свойств (основной)
        2. Штраф за превышение стоимости
        3. Штраф за сумму компонентов != 100%
        4. Штраф за невалидные значения

        Args:
            x: Вектор значений элементов

        Returns:
            Значение fitness (меньше = лучше)
        """
        # Преобразуем вектор в состав
        composition = self._vector_to_composition(x)

        # Проверка суммы компонентов
        total = sum(composition.values())
        if abs(total - 100) > 10:
            return 1e6  # Сильный штраф за невалидную сумму

        # Штраф за отклонение от 100%
        sum_penalty = (total - 100) ** 2 * 0.1

        # Прогнозируем свойства
        try:
            from ..schemas.composition import AlloyComposition
            alloy = AlloyComposition(**composition)
            prediction = self.predictor.predict(alloy)
            props = prediction.mechanical_properties
        except Exception as e:
            logger.warning(f"Ошибка прогноза: {e}")
            return 1e6

        # Рассчитываем отклонение от целевых свойств
        property_penalty = 0

        if self.config.target_yield_strength is not None:
            diff = (props.yield_strength_mpa - self.config.target_yield_strength) / self.config.target_yield_strength
            # Штраф больше если свойство НИЖЕ целевого
            if props.yield_strength_mpa < self.config.target_yield_strength:
                property_penalty += diff ** 2 * 10  # Увеличенный штраф
            else:
                property_penalty += diff ** 2  # Меньший штраф за превышение

        if self.config.target_tensile_strength is not None:
            diff = (props.tensile_strength_mpa - self.config.target_tensile_strength) / self.config.target_tensile_strength
            if props.tensile_strength_mpa < self.config.target_tensile_strength:
                property_penalty += diff ** 2 * 10
            else:
                property_penalty += diff ** 2

        if self.config.target_elongation is not None:
            diff = (props.elongation_percent - self.config.target_elongation) / max(1, self.config.target_elongation)
            if props.elongation_percent < self.config.target_elongation:
                property_penalty += diff ** 2 * 5
            else:
                property_penalty += diff ** 2

        if self.config.target_hardness is not None and props.hardness_hrc is not None:
            diff = (props.hardness_hrc - self.config.target_hardness) / max(1, self.config.target_hardness)
            property_penalty += diff ** 2 * 3

        # Штраф за стоимость
        cost = self._calculate_cost(composition)
        max_cost = self._get_max_cost()
        if cost > max_cost:
            cost_penalty = ((cost - max_cost) / max_cost) ** 2 * 100
        else:
            cost_penalty = 0

        # Итоговый fitness
        fitness = property_penalty + sum_penalty + cost_penalty

        # Сохраняем хорошие решения для альтернатив
        if fitness < 10:
            self._best_solutions.append((composition.copy(), fitness))

        return fitness

    def optimize(self, config: OptimizationConfig) -> Dict:
        """
        Выполнить оптимизацию состава.

        Args:
            config: Конфигурация оптимизации

        Returns:
            Словарь с результатами:
            - optimal_composition: Оптимальный состав
            - predicted_properties: Прогнозируемые свойства
            - fitness_score: Оценка соответствия (0-1)
            - alternatives: Альтернативные составы
            - optimization_stats: Статистика оптимизации
        """
        self.config = config
        self._best_solutions = []

        logger.info(f"Начинаю оптимизацию. Цели: YS={config.target_yield_strength}, "
                   f"TS={config.target_tensile_strength}, El={config.target_elongation}")

        # Получаем границы
        bounds = self._get_bounds()

        # Запускаем дифференциальную эволюцию
        result: OptimizeResult = differential_evolution(
            func=self._fitness_function,
            bounds=bounds,
            strategy='best1bin',           # Стратегия мутации
            maxiter=config.max_iterations,
            popsize=config.population_size // len(OPTIMIZATION_ELEMENTS),
            tol=config.tolerance,
            mutation=(0.5, 1.0),           # Коэффициент мутации
            recombination=0.7,             # Вероятность кроссовера
            seed=42,                       # Для воспроизводимости
            polish=True,                   # Локальная оптимизация в конце
            workers=1,                     # Параллелизация (1 = последовательно)
            updating='deferred',           # Обновление популяции
        )

        # Получаем оптимальный состав
        optimal_composition = self._vector_to_composition(result.x)

        # Прогнозируем свойства для оптимального состава
        from ..schemas.composition import AlloyComposition
        alloy = AlloyComposition(**optimal_composition)
        prediction = self.predictor.predict(alloy)

        # Формируем альтернативы (уникальные, отсортированные по fitness)
        seen = set()
        alternatives = []

        for comp, fitness in sorted(self._best_solutions, key=lambda x: x[1]):
            comp_key = tuple(sorted(comp.items()))
            if comp_key not in seen and len(alternatives) < config.num_alternatives:
                seen.add(comp_key)

                # Прогноз для альтернативы
                try:
                    alt_alloy = AlloyComposition(**comp)
                    alt_pred = self.predictor.predict(alt_alloy)
                    alternatives.append({
                        "composition": comp,
                        "predicted_properties": {
                            "yield_strength_mpa": alt_pred.mechanical_properties.yield_strength_mpa,
                            "tensile_strength_mpa": alt_pred.mechanical_properties.tensile_strength_mpa,
                            "elongation_percent": alt_pred.mechanical_properties.elongation_percent,
                            "hardness_hrc": alt_pred.mechanical_properties.hardness_hrc,
                        },
                        "fitness_score": round(max(0, 1 - fitness / 10), 3),
                        "cost_level": self._get_cost_level(comp),
                    })
                except Exception:
                    pass

        # Рассчитываем fitness_score (0-1, больше = лучше)
        fitness_score = max(0, min(1, 1 - result.fun / 10))

        logger.info(f"Оптимизация завершена. Fitness: {result.fun:.4f}, "
                   f"Score: {fitness_score:.2f}, Iterations: {result.nit}")

        return {
            "optimal_composition": optimal_composition,
            "predicted_properties": prediction.mechanical_properties,
            "fitness_score": round(fitness_score, 3),
            "alternatives": alternatives[:config.num_alternatives],
            "optimization_stats": {
                "iterations": result.nit,
                "function_evaluations": result.nfev,
                "success": result.success,
                "message": result.message,
            }
        }

    def _get_cost_level(self, composition: Dict[str, float]) -> str:
        """Определить уровень стоимости состава."""
        cost = self._calculate_cost(composition)
        if cost < 5:
            return "low"
        elif cost < 15:
            return "medium"
        else:
            return "high"


# Singleton для оптимизатора
_optimizer: Optional[AlloyOptimizer] = None


def get_optimizer() -> AlloyOptimizer:
    """Получить экземпляр оптимизатора."""
    global _optimizer
    if _optimizer is None:
        from .predictor import get_predictor
        _optimizer = AlloyOptimizer(get_predictor())
    return _optimizer
