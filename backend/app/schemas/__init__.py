"""Pydantic схемы для API."""

from .composition import AlloyComposition, CompositionInput
from .prediction import (
    MechanicalProperties,
    AlloyBehavior,
    AlloyClassification,
    PredictionResponse,
    OptimizationRequest,
    OptimizationResponse,
)

__all__ = [
    "AlloyComposition",
    "CompositionInput",
    "MechanicalProperties",
    "AlloyBehavior",
    "AlloyClassification",
    "PredictionResponse",
    "OptimizationRequest",
    "OptimizationResponse",
]
