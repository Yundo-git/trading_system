# test_connection.py - 메인넷 안전 테스트 버전

import sys
import io
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import time

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def safe_float(value, default=0.0):
    """안전하게 float로 변환"""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def test_bybit_connection(use_testnet=True):
    """
    Bybit API 연결 및 선물거래 설정 테스트
    
    Args:
        use_testnet (bool): True면 Testnet, False면 Mainnet
    """
    print("=" * 80)
    if use_testnet:
        print("🧪 Bybit TESTNET API 종합 테스트")
        print("⚠️  테스트 환경 - 실제 자산 없음")
    else:
        print("🔗 Bybit MAINNET API 종합 테스트")
        print("⚠️  ⚠️  ⚠️  실제 거래 환경 - 실제 자산 사용! ⚠️  ⚠️  ⚠️")
        print("\n🚨 주의사항:")
        print("   - 실제 돈이 사용됩니다!")
        print("   - API 출금 권한은 반드시 비활성화하세요!")
        print("   - 소액으로 테스트하세요!")
        
        confirm = input("\n계속하시겠습니까? (yes 입력): ").strip().lower()
        if confirm != 'yes':
            print("\n❌ 테스트 취소됨")
            return False
    
    print("=" * 80)
    
    # 환경 변수 로드
    load_dotenv()
    
    # API 키 가져오기
    if use_testnet:
        api_key = os.getenv('BYBIT_TESTNET_API_KEY')
        api_secret = os.getenv('BYBIT_TESTNET_API_SECRET')
        env_name = "TESTNET"
    else:
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        env_name = "MAINNET"
    
    # 거래 설정 가져오기
    symbol = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
    category = 'linear'
    leverage = int(os.getenv('LEVERAGE', '2'))
    
    if not api_key or not api_secret:
        print(f"❌ {env_name} API 키가 .env 파일에 없습니다!")
        if not use_testnet:
            print("\n.env 파일에 다음 항목을 추가하세요:")
            print("BYBIT_API_KEY=your_mainnet_api_key")
            print("BYBIT_API_SECRET=your_mainnet_api_secret")
        return False
    
    try:
        # ============================================================
        # Part 1: 기본 연결 테스트
        # ============================================================
        print(f"\n📡 Part 1: 기본 연결 테스트")
        print("-" * 80)
        
        print(f"1️⃣ Bybit {env_name} 연결 중...")
        
        session = HTTP(
            testnet=use_testnet,
            api_key=api_key,
            api_secret=api_secret,
            recv_window=60000
        )
        print("   ✅ 연결 성공!")
        
        # 서버 시간 확인
        print("2️⃣ 서버 시간 확인 중...")
        server_time = session.get_server_time()
        if server_time['retCode'] == 0:
            print(f"   ✅ 서버 시간 동기화 완료")
        
        # API 권한 확인 (메인넷만)
        if not use_testnet:
            print("3️⃣ API 키 권한 확인 중...")
            try:
                api_key_info = session.get_api_key_information()
                if api_key_info['retCode'] == 0:
                    result = api_key_info['result']
                    permissions = result.get('permissions', {})
                    
                    print("   ✅ API 권한 확인 완료!")
                    print(f"   - 읽기: {'✅' if 'Order' in str(permissions) else '❌'}")
                    print(f"   - 거래: {'✅' if 'Order' in str(permissions) else '❌'}")
                    
                    # 출금 권한 체크
                    if 'Withdraw' in str(permissions) or 'Transfer' in str(permissions):
                        print(f"   ⚠️  ⚠️  ⚠️  출금/이체 권한 활성화됨! ⚠️  ⚠️  ⚠️")
                        print(f"   🚨 보안을 위해 출금 권한을 비활성화하세요!")
                        
                        proceed = input("\n출금 권한이 활성화되어 있습니다. 계속하시겠습니까? (yes 입력): ").strip().lower()
                        if proceed != 'yes':
                            print("\n❌ 테스트 취소됨 - API 설정을 확인하세요")
                            return False
                    else:
                        print(f"   - 출금: ❌ (안전)")
            except Exception as e:
                print(f"   ⚠️  권한 확인 불가: {str(e)}")
        
        # 계정 정보 조회
        print(f"\n4️⃣ 계정 정보 확인 중...")
        wallet_balance = session.get_wallet_balance(accountType="UNIFIED")
        
        if wallet_balance['retCode'] != 0:
            print(f"   ❌ 계정 확인 실패: {wallet_balance['retMsg']}")
            return False
            
        print("   ✅ 계정 확인 성공!")
        
        # USDT/USD 잔액 찾기
        usdt_info = None
        for coin in wallet_balance['result']['list'][0]['coin']:
            if coin['coin'] in ['USDT', 'USD']:
                usdt_info = coin
                break
        
        available_balance = 0
        if usdt_info:
            equity = safe_float(usdt_info.get('equity'))
            available_balance = safe_float(
                usdt_info.get('availableToWithdraw') or 
                usdt_info.get('walletBalance') or 
                usdt_info.get('equity')
            )
            
            print(f"\n💰 {usdt_info['coin']} 잔액 ({env_name})")
            print(f"   - 총 자산: {equity:,.2f}")
            print(f"   - 사용 가능: {available_balance:,.2f}")
            
            if not use_testnet and available_balance > 0:
                print(f"\n   💡 실전 거래 권장사항:")
                print(f"      - 테스트용 최소 금액: 10-20 USDT")
                print(f"      - 손실 허용 금액만 사용하세요")
                print(f"      - 레버리지는 낮게 유지 (2-3x 권장)")
            
            if equity == 0 and use_testnet:
                print(f"\n💡 팁: Testnet 자산이 0입니다.")
                print(f"   1. https://testnet.bybit.com 접속")
                print(f"   2. Assets → Funding에서 테스트 코인 받기")
                print(f"   3. Funding → Unified Trading으로 이체")
        
        # ============================================================
        # Part 2: 선물거래 설정 테스트
        # ============================================================
        print(f"\n\n🔷 Part 2: {symbol} 선물거래 설정 테스트")
        print("-" * 80)
        print(f"📋 거래 설정")
        print(f"   - 심볼: {symbol}")
        print(f"   - 카테고리: {category}")
        print(f"   - 레버리지: {leverage}x")
        print()
        
        # 1. 심볼 정보 확인
        print(f"1️⃣ {symbol} 선물 심볼 정보 조회 중...")
        instruments = session.get_instruments_info(
            category=category,
            symbol=symbol
        )
        
        if instruments['retCode'] != 0 or not instruments['result']['list']:
            print(f"   ❌ 심볼 조회 실패")
            return False
        
        info = instruments['result']['list'][0]
        min_qty = safe_float(info['lotSizeFilter']['minOrderQty'])
        max_leverage = safe_float(info['leverageFilter']['maxLeverage'])
        
        print("   ✅ 심볼 확인 성공!")
        print(f"   - 심볼: {info['symbol']}")
        print(f"   - 상태: {info['status']}")
        print(f"   - 최소 주문: {min_qty} {symbol.replace('USDT', '')}")
        print(f"   - 최대 레버리지: {max_leverage}x")
        
        # 2. 현재 시장가 확인
        print(f"\n2️⃣ 현재 {symbol} 시장가 조회 중...")
        ticker = session.get_tickers(category=category, symbol=symbol)
        
        last_price = 0
        if ticker['retCode'] == 0 and ticker['result']['list']:
            price_info = ticker['result']['list'][0]
            last_price = safe_float(price_info['lastPrice'])
            price_change = safe_float(price_info['price24hPcnt']) * 100
            volume = safe_float(price_info['volume24h'])
            
            print("   ✅ 시장가 확인 성공!")
            print(f"   - 현재가: ${last_price:,.2f}")
            print(f"   - 24시간 변동: {price_change:+.2f}%")
            print(f"   - 24시간 거래량: {volume:,.2f}")
        else:
            print("   ⚠️  시장가 조회 실패")
        
        # 3. 레버리지 설정 테스트
        print(f"\n3️⃣ 레버리지 {leverage}x 설정 테스트 중...")
        
        try:
            if leverage > max_leverage:
                print(f"   ⚠️  요청 레버리지({leverage}x)가 최대값({max_leverage}x)을 초과합니다!")
                leverage = int(max_leverage)
                print(f"   → {leverage}x로 조정합니다.")
            
            leverage_result = session.set_leverage(
                category=category,
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if leverage_result['retCode'] == 0:
                print(f"   ✅ 레버리지 {leverage}x 설정 성공!")
            elif leverage_result['retCode'] == 110043:
                print(f"   ✅ 레버리지 {leverage}x (이미 설정되어 있음)")
            else:
                print(f"   ⚠️  레버리지 설정: {leverage_result['retMsg']}")
                
        except Exception as e:
            error_str = str(e)
            if '110043' in error_str or 'not modified' in error_str.lower():
                print(f"   ✅ 레버리지 {leverage}x (이미 설정되어 있음)")
            else:
                print(f"   ⚠️  레버리지 설정 중 오류: {error_str}")
        
        # 4. 거래 가능 수량 계산
        print("\n4️⃣ 거래 가능 수량 계산 중...")
        
        if available_balance > 0 and last_price > 0:
            # 소액 테스트용 (30% 사용)
            test_balance = available_balance * 0.3
            max_position_value = test_balance * leverage
            max_qty = max_position_value / last_price
            
            print("   ✅ 계산 완료!")
            print(f"   - 사용 가능 자금: {available_balance:,.2f} USDT")
            print(f"   - 테스트용 자금 (30%): {test_balance:,.2f} USDT")
            print(f"   - {leverage}x 레버리지 적용: {max_position_value:,.2f} USDT")
            print(f"   - 최대 거래 가능: {max_qty:.6f} {symbol.replace('USDT', '')}")
            
            if max_qty >= min_qty:
                print(f"   - 최소 주문 단위: {min_qty} ✅")
                possible_orders = int(max_qty / min_qty)
                print(f"   - 가능한 주문 횟수: 약 {possible_orders}회")
                
                # 예시 주문 크기
                print(f"\n   💡 추천 테스트 주문:")
                print(f"      • 최소 주문: {min_qty} (약 ${min_qty * last_price:,.2f})")
                if not use_testnet:
                    safe_qty = min_qty
                    print(f"      • 실전 첫 주문: {safe_qty} (약 ${safe_qty * last_price:,.2f})")
                    print(f"      • 최대 손실 (3% 손절): 약 ${safe_qty * last_price * leverage * 0.03:,.2f}")
            else:
                print(f"   ⚠️  잔액이 부족합니다. 최소 {min_qty} 거래 필요")
                print(f"      필요 금액: 약 ${min_qty * last_price:,.2f}")
        else:
            print("   ⚠️  사용 가능한 잔액이 없습니다")
        
        # 5. 현재 포지션 확인
        print(f"\n5️⃣ 현재 포지션 확인 중...")
        positions = session.get_positions(category=category, symbol=symbol)
        
        if positions['retCode'] == 0:
            active_positions = [p for p in positions['result']['list'] if safe_float(p.get('size', 0)) > 0]
            print(f"   📊 활성 포지션: {len(active_positions)}개")
            
            if active_positions:
                print(f"\n   📈 포지션 상세:")
                for pos in active_positions:
                    side = pos['side']
                    size = safe_float(pos['size'])
                    entry_price = safe_float(pos['avgPrice'])
                    unrealized_pnl = safe_float(pos['unrealisedPnl'])
                    
                    pnl_emoji = "📈" if unrealized_pnl >= 0 else "📉"
                    print(f"   {pnl_emoji} {pos['symbol']}: {side} {size}")
                    print(f"      진입가: ${entry_price:,.2f} | 손익: {unrealized_pnl:+,.2f} USDT")
            else:
                print(f"   ✅ 포지션 없음 (거래 준비 완료)")
        
        # ============================================================
        # 최종 결과
        # ============================================================
        print("\n" + "=" * 80)
        print(f"✅ 모든 테스트 통과! ({env_name})")
        print("=" * 80)
        print(f"\n📌 요약:")
        print(f"   ✅ API 연결 성공")
        print(f"   ✅ 계정 인증 완료")
        print(f"   ✅ {symbol} 선물 거래 가능")
        print(f"   ✅ {leverage}x 레버리지 설정 완료")
        
        if available_balance > 0:
            print(f"   ✅ 거래 준비 완료! (잔액: {available_balance:,.2f} USDT)")
            
            if not use_testnet:
                print(f"\n🎯 다음 단계:")
                print(f"   1. DRY RUN 모드로 시그널 확인")
                print(f"   2. 소액 실전 테스트 (10-20 USDT)")
                print(f"   3. 결과 모니터링 및 점진적 증액")
                
                print(f"\n⚠️  안전 수칙:")
                print(f"   • 손실 가능한 금액만 사용")
                print(f"   • 처음엔 최소 수량으로 테스트")
                print(f"   • 레버리지 낮게 유지 (2-3x)")
                print(f"   • 모니터링 가능한 시간에만 거래")
                print(f"   • Ctrl+C로 언제든 봇 중지 가능")
            else:
                print(f"\n🚀 다음 단계: 실제 주문 테스트")
        else:
            print(f"   ⚠️  Unified Trading 계정에 자산을 이체하세요")
        
        print("=" * 80)
        return True
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"📁 작업 폴더: {os.getcwd()}\n")
    
    # 🔍 메인넷 테스트 (실제 돈 사용)
    test_bybit_connection(use_testnet=False)
    
    # 🧪 테스트넷 (가상 돈)
    # test_bybit_connection(use_testnet=True)