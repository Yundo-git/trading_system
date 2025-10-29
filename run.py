"""
Trading System 실행 스크립트

사용법:
    python run.py
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],  # app 디렉토리 변경 시 자동 리로드
        workers=1
    )
