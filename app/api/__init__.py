"""
API 라우터 설정
"""
from fastapi import APIRouter
from .endpoints import trading

# API 라우터 생성
api_router = APIRouter()

# 라우터 등록
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
