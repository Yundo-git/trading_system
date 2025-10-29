"""
표준 출력을 WebSocket으로 리다이렉트하는 로거
"""
import sys
import asyncio
import logging
from typing import Optional
from ..websocket.log_manager import log_manager

# 로거 설정
logger = logging.getLogger(__name__)

class WebSocketLogger:
    """표준 출력을 WebSocket으로 리다이렉트하는 클래스"""
    
    def __init__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.websocket_stdout = WebSocketStdOut()
        self.websocket_stderr = WebSocketStdErr()
        self.is_redirected = False
    
    def start_redirect(self):
        """표준 출력을 WebSocket으로 리다이렉트 시작"""
        if not self.is_redirected:
            sys.stdout = self.websocket_stdout
            sys.stderr = self.websocket_stderr
            self.is_redirected = True
    
    def stop_redirect(self):
        """표준 출력 복원"""
        if self.is_redirected:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            self.is_redirected = False

class WebSocketStdOut:
    """WebSocket으로 출력하는 표준 출력 클래스"""
    
    def write(self, message: str):
        """메시지를 WebSocket으로 전송"""
        if message.strip():
            asyncio.create_task(log_manager.broadcast_log(message))
        return len(message)
    
    def flush(self):
        """버퍼 플러시 (필수 메서드)"""
        pass

class WebSocketStdErr(WebSocketStdOut):
    """에러 메시지를 WebSocket으로 출력하는 클래스"""
    pass

# 전역 인스턴스 생성
websocket_logger = WebSocketLogger()

# 애플리케이션 시작 시 로거 초기화
async def initialize_logger():
    """WebSocket 로거 초기화"""
    websocket_logger.start_redirect()
    logger.info("WebSocket logger initialized")

# 애플리케이션 종료 시 로거 정리
async def cleanup_logger():
    """WebSocket 로거 정리"""
    websocket_logger.stop_redirect()
    logger.info("WebSocket logger cleaned up")
