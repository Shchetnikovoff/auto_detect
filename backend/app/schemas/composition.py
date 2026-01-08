"""Схемы для химического состава сплава."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class AlloyComposition(BaseModel):
    """Химический состав сплава (в процентах)."""

    # Основные элементы
    Fe: float = Field(default=0.0, ge=0, le=100, description="Железо (%)")
    C: float = Field(default=0.0, ge=0, le=5, description="Углерод (%)")
    Si: float = Field(default=0.0, ge=0, le=5, description="Кремний (%)")
    Mn: float = Field(default=0.0, ge=0, le=20, description="Марганец (%)")

    # Легирующие элементы
    Cr: float = Field(default=0.0, ge=0, le=30, description="Хром (%)")
    Ni: float = Field(default=0.0, ge=0, le=40, description="Никель (%)")
    Mo: float = Field(default=0.0, ge=0, le=10, description="Молибден (%)")
    V: float = Field(default=0.0, ge=0, le=5, description="Ванадий (%)")
    W: float = Field(default=0.0, ge=0, le=20, description="Вольфрам (%)")
    Co: float = Field(default=0.0, ge=0, le=30, description="Кобальт (%)")
    Ti: float = Field(default=0.0, ge=0, le=5, description="Титан (%)")
    Al: float = Field(default=0.0, ge=0, le=100, description="Алюминий (%)")
    Cu: float = Field(default=0.0, ge=0, le=10, description="Медь (%)")
    Nb: float = Field(default=0.0, ge=0, le=5, description="Ниобий (%)")

    # Примеси
    P: float = Field(default=0.0, ge=0, le=1, description="Фосфор (%)")
    S: float = Field(default=0.0, ge=0, le=1, description="Сера (%)")
    N: float = Field(default=0.0, ge=0, le=1, description="Азот (%)")

    @field_validator("*", mode="before")
    @classmethod
    def round_values(cls, v):
        """Округление значений до 4 знаков."""
        if isinstance(v, (int, float)):
            return round(float(v), 4)
        return v

    def total_percent(self) -> float:
        """Суммарный процент всех элементов."""
        return sum([
            self.Fe, self.C, self.Si, self.Mn, self.Cr, self.Ni,
            self.Mo, self.V, self.W, self.Co, self.Ti, self.Al,
            self.Cu, self.Nb, self.P, self.S, self.N
        ])

    def to_feature_vector(self) -> list[float]:
        """Преобразование в вектор признаков для ML модели."""
        return [
            self.Fe, self.C, self.Si, self.Mn, self.Cr, self.Ni,
            self.Mo, self.V, self.W, self.Co, self.Ti, self.Al,
            self.Cu, self.Nb, self.P, self.S, self.N
        ]

    @classmethod
    def feature_names(cls) -> list[str]:
        """Названия признаков."""
        return [
            "Fe", "C", "Si", "Mn", "Cr", "Ni",
            "Mo", "V", "W", "Co", "Ti", "Al",
            "Cu", "Nb", "P", "S", "N"
        ]


class CompositionInput(BaseModel):
    """Входные данные для прогнозирования."""

    composition: AlloyComposition = Field(..., description="Химический состав сплава")

    # Опциональные параметры обработки
    heat_treatment: Optional[str] = Field(
        default=None,
        description="Тип термообработки (annealed, normalized, quenched, tempered)"
    )
    temperature_c: Optional[float] = Field(
        default=None,
        ge=0,
        le=2000,
        description="Температура обработки (°C)"
    )
