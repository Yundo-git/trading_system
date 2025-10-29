"""
트레이딩 봇 서비스 - FastAPI와 통합된 트레이딩 봇 관리
"""
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import sys
import importlib.util
import logging
from ..websocket.log_manager import log_manager

logger = logging.getLogger(__name__)

class TradingBotService:
    """트레이딩 봇 서비스 클래스"""
    
    def __init__(self):
        self.bot = None
        self.bot_task = None
        self.is_running = False
        self.bot_module = None
        self.bot_class = None
        
        # 트레이딩 봇 모듈 로드
        self._load_bot_module()
    
    def _load_bot_module(self):
        """
        트레이딩 봇 모듈을 안전하게 동적으로 로드합니다.
        
        Returns:
            bool: 모듈 로드 성공 여부
        """
        try:
            # 프로젝트 루트를 Python 경로에 추가
            root_dir = str(Path(__file__).parent.parent)
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)  # 맨 앞에 추가하여 우선순위 부여
            
            # 모듈 경로 출력 (디버깅용)
            logger.info(f"Python path: {sys.path}")
            
            # 모듈 직접 임포트 (절대 경로 사용)
            try:
                from app.trading.live_trading_bot import LiveTradingBot
                self.bot_class = LiveTradingBot
                logger.info("Successfully loaded LiveTradingBot class")
                return True
                
            except ImportError as ie:
                logger.error(f"Failed to import LiveTradingBot: {str(ie)}")
                logger.error(f"Current sys.path: {sys.path}")
                self.bot_class = None
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error in _load_bot_module: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            self.bot_class = None
            return False
    
    async def start(self, symbol: str = "ETHUSDT", leverage: int = 2, dry_run: bool = True):
        """트레이딩 봇 시작"""
        if self.is_running:
            return {"status": "error", "message": "이미 실행 중인 트레이딩 봇이 있습니다."}
        
        try:
            # 트레이딩 봇 인스턴스 생성
            self.bot = self.bot_class(
                symbol=symbol,
                leverage=leverage,
                dry_run=dry_run
            )
            
            # WebSocket 로거 설정 (기존 print 대체)
            if hasattr(self.bot, 'log'):
                original_log = self.bot.log
                async def wrapped_log(message):
                    await original_log(message)
                    await log_manager.broadcast_log(message)
                self.bot.log = wrapped_log
            
            # 비동기로 트레이딩 봇 실행
            self.bot_task = asyncio.create_task(self._run_bot())
            self.is_running = True
            
            return {
                "status": "success",
                "message": "트레이딩 봇이 시작되었습니다.",
                "symbol": symbol,
                "leverage": leverage,
                "dry_run": dry_run
            }
            
        except Exception as e:
            logger.error(f"트레이딩 봇 시작 실패: {e}")
            return {"status": "error", "message": f"트레이딩 봇 시작 실패: {str(e)}"}
    
    async def _run_bot(self):
        """트레이딩 봇 실행 (비동기)"""
        try:
            await log_manager.broadcast_log("트레이딩 봇을 시작합니다...")
            await self.bot.run()
        except asyncio.CancelledError:
            await log_manager.broadcast_log("트레이딩 봇이 중지되었습니다.")
        except Exception as e:
            error_msg = f"트레이딩 봇 실행 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            await log_manager.broadcast_log(error_msg)
        finally:
            self.is_running = False
    
    async def stop(self):
        """트레이딩 봇 중지"""
        if not self.is_running or not self.bot_task:
            return {"status": "error", "message": "실행 중인 트레이딩 봇이 없습니다."}
        
        try:
            self.bot_task.cancel()
            await self.bot_task
            self.is_running = False
            
            return {"status": "success", "message": "트레이딩 봇이 중지되었습니다."}
            
        except Exception as e:
            error_msg = f"트레이딩 봇 중지 중 오류: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def get_status(self) -> Dict[str, Any]:
        """트레이딩 봇 상태 조회"""
        if not self.is_running or not self.bot:
            return {
                "status": "not_running",
                "is_running": False
            }
        
        # 트레이딩 봇에서 상태 정보 가져오기
        status = {
            "status": "running",
            "is_running": True,
            "symbol": getattr(self.bot, 'symbol', 'N/A'),
            "leverage": getattr(self.bot, 'leverage', 'N/A'),
            "dry_run": getattr(self.bot, 'dry_run', True)
        }
        
        # 포지션 정보가 있다면 추가
        if hasattr(self.bot, 'position') and self.bot.position:
            status["position"] = self.bot.position
            
        return status

# 서비스 인스턴스 (지연 로딩용)
_trading_bot_service = None

def get_trading_bot_service():
    """트레이딩 봇 서비스 인스턴스를 가져옵니다."""
    global _trading_bot_service
    if _trading_bot_service is None:
        _trading_bot_service = TradingBotService()
    return _trading_bot_service
