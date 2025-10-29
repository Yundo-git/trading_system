"""
WebSocket 연결 관리자 (connection_manager.py)
"""
from typing import Dict, List, Any
from fastapi import WebSocket
import json
from datetime import datetime
import logging
import uuid # client_id를 생성할 경우 필요

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결을 관리하고 메시지를 브로드캐스팅하는 클래스"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """새로운 WebSocket 연결을 등록합니다. (Accept 호출 제거)"""
        # 🟢 수정 완료: 라우터에서 accept()를 처리하도록 accept() 호출 제거
        self.active_connections[client_id] = websocket
        logger.info(f"새 클라이언트 연결 등록: {client_id}")

    def disconnect(self, client_id: str):
        """WebSocket 연결을 해제하고 관련된 모든 구독을 정리합니다."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # 모든 구독에서 클라이언트 제거
            for symbol, clients in list(self.subscriptions.items()):
                if client_id in clients:
                    clients.remove(client_id)
                if not clients:
                    del self.subscriptions[symbol]
            logger.info(f"클라이언트 연결 종료 및 등록 해제: {client_id}")

    async def subscribe(self, client_id: str, symbol: str):
        """클라이언트를 특정 심볼의 구독자로 등록합니다."""
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = []
        if client_id not in self.subscriptions[symbol]:
            self.subscriptions[symbol].append(client_id)
            logger.info(f"클라이언트 {client_id}가 {symbol} 구독 시작")

    async def broadcast(self, symbol: str, message: Dict[str, Any]) -> None:
        """특정 심볼을 구독한 모든 클라이언트에게 메시지를 전송합니다."""
        if symbol not in self.subscriptions:
            return
            
        message_str = json.dumps({
            "type": "trading_update",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": message
        })
        
        disconnected_clients = []
        
        for client_id in self.subscriptions[symbol]:
            try:
                if client_id in self.active_connections:
                    await self.active_connections[client_id].send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            self.disconnect(client_id)

manager = ConnectionManager()