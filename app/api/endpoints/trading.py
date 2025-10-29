"""
트레이딩 봇 상태 확인 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from ...services.trading_bot_service import get_trading_bot_service, TradingBotService

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_trading_status(
    request: Request,
    bot_service: TradingBotService = Depends(get_trading_bot_service)
) -> JSONResponse:
    """
    트레이딩 봇 상태 조회
    """
    try:
        # CORS 헤더 설정
        origin = request.headers.get("origin")
        headers = {
            "Access-Control-Allow-Origin": origin or "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
        
        # 🟢 봇 서비스 인스턴스를 통해 실제 상태를 조회합니다.
        is_running = getattr(bot_service, 'is_running', False)
        is_initialized = getattr(bot_service, 'is_initialized', False)
        
        # 상태 메시지 결정
        if is_running:
            status_message = "online"
        elif is_initialized:
            status_message = "initialized"
        else:
            status_message = "service_not_initialized"

        # 응답 데이터 준비
        response_data = {
            "is_running": is_running,
            "status": status_message,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
        return JSONResponse(
            content=response_data,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Error in get_trading_status: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"상태 확인 중 오류 발생: {str(e)}"},
            headers=headers
        )

# OPTIONS 메서드 핸들러 추가
@router.options("/status")
async def options_status():
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )