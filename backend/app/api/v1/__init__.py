"""API v1 роутеры."""

from fastapi import APIRouter

from .predict import router as predict_router
from .reference import router as reference_router

api_router = APIRouter()

api_router.include_router(predict_router, prefix="/predict", tags=["predict"])
api_router.include_router(reference_router, prefix="/reference", tags=["reference"])
