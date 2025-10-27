# config.py
# ⚠️ 이 파일은 절대 공유하지 마세요!
# ⚠️ GitHub에 업로드 금지!

"""
Bybit API 설정
생성일: 2025-10-20
용도: Phase 2 자동매매
"""

# ==================== Bybit API Keys ====================
# 본계정 (실전용 - Phase 2.2)
BYBIT_API_KEY = "여기에_발급받은_API_Key_붙여넣기"
BYBIT_API_SECRET = "여기에_발급받은_Secret_붙여넣기"

# 테스트넷 (연습용 - Phase 2.1)
BYBIT_TESTNET_API_KEY = "W2axB014c0j5bZHSOO".strip()  # 나중에 테스트넷 키 발급 시 입력
BYBIT_TESTNET_API_SECRET = "yYmh6Nf6jiDXxVD6h2OZKH7LYE8CkhU5IPNn".strip()

# ==================== 거래 설정 ====================
# 심볼
SYMBOL = "ETH/USDT:USDT"  # Bybit 선물 심볼

# 레버리지
LEVERAGE = 2  # 2배 고정

# 초기 자본 (Phase 2.2 실전 시)
INITIAL_CAPITAL = 500  # USDT

# 안전장치
SAFETY_LIMITS = {
    "max_daily_loss": -0.05,          # 일일 최대 손실 5%
    "max_position_size": 0.3,         # 최대 포지션 30%
    "max_daily_trades": 3,            # 일일 최대 거래 3회
    "max_consecutive_losses": 3,      # 연속 손실 3회 시 중단
}

# ==================== 텔레그램 알림 (선택사항) ====================
TELEGRAM_BOT_TOKEN = ""  # 나중에 설정
TELEGRAM_CHAT_ID = ""    # 나중에 설정

# ==================== 보안 체크 ====================
def check_config():
    """설정 확인"""
    if "여기에" in BYBIT_API_KEY or not BYBIT_API_KEY:
        print("⚠️  API Key를 입력하세요!")
        return False
    
    if "여기에" in BYBIT_API_SECRET or not BYBIT_API_SECRET:
        print("⚠️  API Secret을 입력하세요!")
        return False
    
    print("✅ Config 설정 완료!")
    return True

if __name__ == "__main__":
    check_config()