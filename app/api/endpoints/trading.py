"""
트레이딩 봇 상태 확인 API
"""
import os
import sys
import psutil
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from ...services.trading_bot_service import get_trading_bot_service, TradingBotService

# 로거 설정
logger = logging.getLogger(__name__)

def is_bot_running() -> bool:
    """Check if live_trading_bot.py is running as a separate process"""
    try:
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Skip current process
                if proc.info['pid'] == current_pid:
                    continue
                    
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:  # Skip if no command line
                    continue
                    
                # Convert cmdline to string for case-insensitive search
                cmdline_str = ' '.join(cmdline).lower()
                if ('python' in cmdline[0].lower() and 
                    'live_trading_bot.py' in cmdline_str):
                    return True
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.warning(f"Error checking process {proc.info.get('pid')}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in is_bot_running: {e}")
        
    return False

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
        
        # Check if live_trading_bot.py is running as a separate process
        bot_process_running = is_bot_running()
        
        # 응답 데이터 준비
        response_data = {
            "is_running": bot_process_running,
            "status": "running" if bot_process_running else "stopped",
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