"""
WebSocket을 통한 실시간 로그 전송을 담당하는 모듈 (log_manager.py)
"""
from typing import List, Optional
from fastapi import WebSocket
import asyncio
import json
from datetime import datetime
import logging
import sys

logger = logging.getLogger(__name__)

class LogWebSocketManager:
    """WebSocket을 통해 실시간 로그를 전송하는 매니저"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        """새로운 WebSocket 연결을 등록합니다. (Accept 호출 제거)"""
        # 🟢 수정 완료: 라우터에서 accept()를 처리하도록 accept() 호출 제거
        self.active_connections.append(websocket)
        logger.info("New WebSocket connection registered")

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결을 해제합니다."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket connection closed and unregistered")

    async def _process_log_queue(self):
        """로그 큐를 처리하는 내부 메서드"""
        while self._is_running:
            try:
                message = await self.log_queue.get()
                if not self.active_connections:
                    continue
                    
                log_data = {
                    "type": "log",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "message": message.strip()
                }
                
                disconnected = []
                for connection in self.active_connections:
                    try:
                        await connection.send_json(log_data)
                    except Exception as e:
                        logger.error(f"Error sending log to client: {e}")
                        disconnected.append(connection)
                        
                # 연결 해제된 클라이언트 정리
                for connection in disconnected:
                    self.disconnect(connection)
                    
            except asyncio.CancelledError:
                logger.info("Log processing task was cancelled")
                break
            except Exception as e:
                logger.error(f"Error in log processing task: {e}", exc_info=True)
                await asyncio.sleep(1)  # 에러 발생 시 잠시 대기 후 재시도
    
    async def start(self):
        """로그 처리 태스크 시작"""
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._process_log_queue())
            logger.info("Log manager started")
    
    async def stop(self):
        """로그 처리 태스크 중지"""
        if self._is_running:
            self._is_running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None
            logger.info("Log manager stopped")
    
    async def broadcast_log(self, message: str):
        """
        모든 연결된 클라이언트에 로그 메시지를 전송합니다.
        
        Args:
            message: 전송할 로그 메시지
        """
        if not message or not isinstance(message, str):
            return
            
        try:
            # 로그 큐에 메시지 추가 (비동기 처리)
            await self.log_queue.put(message)
        except Exception as e:
            logger.error(f"Error adding log to queue: {e}")

    # start_log_consumer, stop_log_consumer 메서드는 이제 사용되지 않음
    # _process_log_queue와 start/stop 메서드로 대체됨

log_manager = LogWebSocketManager()