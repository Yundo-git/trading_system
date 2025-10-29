# app/config.py
"""
애플리케이션 설정
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    # 애플리케이션 설정
    PROJECT_NAME: str = "Trading System Backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API 설정
    API_PREFIX: str = "/api"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]  # 프론트엔드 주소
    
    # Bybit API 설정
    BYBIT_TESTNET: bool = os.getenv("BYBIT_TESTNET", "True").lower() == "true"
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY" if not os.getenv("BYBIT_TESTNET", "True").lower() == "true" else "BYBIT_TESTNET_API_KEY", "")
    BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET" if not os.getenv("BYBIT_TESTNET", "True").lower() == "true" else "BYBIT_TESTNET_API_SECRET", "")
    
    # 거래 설정
    TRADING_SYMBOL: str = os.getenv("TRADING_SYMBOL", "ETHUSDT")
    TRADING_CATEGORY: str = os.getenv("TRADING_CATEGORY", "linear")
    LEVERAGE: int = int(os.getenv("LEVERAGE", "2"))
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trading.db")
    
    # 보안 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일
    
    class Config:
        case_sensitive = True

# 전역 설정 객체
settings = Settings()