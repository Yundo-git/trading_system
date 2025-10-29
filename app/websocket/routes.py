"""
WebSocket 라우터 설정 (routes.py)
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
# 두 매니저 임포트 (파일 경로에 맞게 수정하세요)
from .log_manager import log_manager 
from .connection_manager import manager 

router = APIRouter()
logger = logging.getLogger(__name__)

# ====================================================================
# A. 로그 스트리밍 엔드포인트
# ====================================================================

@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """실시간 로그 스트리밍 엔드포인트"""
    try:
        # 1. 연결 수락 (Accept)
        await websocket.accept()
        
        # 2. log_manager에 연결 등록
        await log_manager.connect(websocket) 
        
        # 3. 통신 유지 루프: 클라이언트 메시지(핑) 수신 대기
        while True:
            try:
                # 45초 타임아웃
                data = await asyncio.wait_for(websocket.receive_text(), timeout=45.0)
                
                # PING/PONG 처리
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat() + "Z"})
                    continue 
                # 기타 클라이언트 메시지 처리...

            except asyncio.TimeoutError:
                logger.warning(f"클라이언트 PING 타임아웃. 연결 종료.")
                break 

            except Exception as e:
                logger.error(f"WebSocket 루프 오류 발생: {str(e)}")
                break 
                
    except WebSocketDisconnect:
        logger.info("WebSocket 연결이 클라이언트에 의해 닫혔습니다.")
        
    except Exception as e:
        logger.error(f"WebSocket 연결 중 치명적 오류 발생: {str(e)}", exc_info=True)
        
    finally:
        # 4. 연결 해제 및 log_manager에서 등록 해제
        log_manager.disconnect(websocket)
        logger.info("WebSocket 핸들러 종료 및 log_manager 등록 해제 완료")

# ====================================================================
# B. 트레이딩 데이터 엔드포인트
# ====================================================================

@router.websocket("/trading")
async def websocket_trading(
    websocket: WebSocket, 
    # 클라이언트 ID가 없는 경우 새로 생성하도록 설정
    client_id: str = Query(default=None) 
):
    """실시간 트레이딩 데이터 브로드캐스트 및 구독 처리 엔드포인트"""
    
    if not client_id:
        client_id = str(uuid.uuid4())
        
    try:
        # 1. 연결 수락 (Accept)
        await websocket.accept() 
        
        # 2. ConnectionManager에 연결 등록
        await manager.connect(websocket, client_id) 
        
        # 3. 클라이언트에게 ID 전송 (클라이언트가 재연결 시 사용할 수 있도록)
        await websocket.send_json({
            "type": "client_id", 
            "client_id": client_id,
            "message": "클라이언트 ID가 할당되었습니다."
        })
        
        # 4. 통신 유지 루프: 클라이언트 메시지(구독/핑) 수신 대기
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 구독 메시지 처리
                if message.get('action') == 'subscribe' and message.get('symbol'):
                    await manager.subscribe(client_id, message['symbol'])
                
                # 핑 메시지 처리 (선택 사항: 클라이언트가 핑을 보내는 경우)
                elif message.get('type') == 'ping':
                    await websocket.send_json({"type": "pong"})
                
                else:
                    logger.warning(f"알 수 없는 메시지 수신: {data}")
                    
            except Exception as e:
                logger.error(f"Trading WS 루프 오류: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"Trading WS 연결 종료: {client_id}")
        
    except Exception as e:
        logger.error(f"Trading WS 연결 중 치명적 오류 발생: {str(e)}", exc_info=True)
        
    finally:
        # 5. 연결 해제 및 등록 해제
        manager.disconnect(client_id)
        logger.info(f"Trading WS 핸들러 종료 및 매니저 등록 해제: {client_id}")