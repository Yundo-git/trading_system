"""
FastAPI 애플리케이션 진입점 (main.py)
"""
import asyncio
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Callable

# 로거 설정
logger = logging.getLogger(__name__)

# .config, .websocket.log_manager, .utils.websocket_logger, .api.endpoints 임포트는 환경에 따라 필요
from .websocket.log_manager import log_manager
from .utils.websocket_logger import websocket_logger
from .api.endpoints import trading

# FastAPI 앱 생성
app = FastAPI(
    title="Trading System API",
    description="암호화폐 트레이딩 시스템 백엔드 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 애플리케이션 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화 작업"""
    try:
        # WebSocket 로그 매니저 시작
        from .websocket.log_manager import log_manager
        from .utils.websocket_logger import initialize_logger
        
        # 로그 매니저 시작
        await log_manager.start()
        logger.info("WebSocket log manager started")
        
        # WebSocket 로거 초기화
        await initialize_logger()
        
        # 트레이딩 서비스 초기화
        from .services.trading_bot_service import get_trading_bot_service
        bot_service = get_trading_bot_service()
        logger.info("Trading bot service initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리 작업"""
    try:
        # WebSocket 로거 정리
        from .utils.websocket_logger import cleanup_logger
        from .websocket.log_manager import log_manager
        
        # WebSocket 로거 정리
        await cleanup_logger()
        
        # WebSocket 로그 매니저 정리
        await log_manager.stop()
        logger.info("WebSocket log manager stopped")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

# CORS 미들웨어 설정 (가장 먼저 등록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# 라우터 등록
from .api import api_router
from .websocket import routes as ws_routes

app.include_router(trading.router, prefix="/trading", tags=["trading"])
app.include_router(api_router, prefix="/api")
app.include_router(ws_routes.router, prefix="/ws") # 웹소켓 라우터 등록

# CORS 헤더를 추가하는 미들웨어
@app.middleware("http")
async def add_cors_headers(request: Request, call_next: Callable):
    # preflight 요청 처리
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)
    
    # CORS 헤더 추가
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response

# OPTIONS 메서드 핸들러
@app.options("/{full_path:path}", include_in_schema=False)
async def options_handler(full_path: str):
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# 상태 확인용 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "Trading System API",
        "version": "0.1.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")