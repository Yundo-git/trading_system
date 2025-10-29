# test_order.py - 빠른 체결 버전

import sys
import io
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def test_order(use_testnet=True):
    print("=" * 60)
    print("🧪 Phase 1.3: 실제 주문 테스트")
    print("⚠️  Testnet - 가짜 돈으로 실제 주문 연습")
    print("=" * 60)
    
    load_dotenv()
    
    api_key = os.getenv('BYBIT_TESTNET_API_KEY')
    api_secret = os.getenv('BYBIT_TESTNET_API_SECRET')
    symbol = os.getenv('TRADING_SYMBOL', 'ETHUSDT')
    category = 'linear'
    
    if not api_key or not api_secret:
        print("❌ API 키가 없습니다!")
        return False
    
    try:
        print("\n📡 Bybit 연결 중...")
        session = HTTP(
            testnet=use_testnet,
            api_key=api_key,
            api_secret=api_secret,
            recv_window=60000
        )
        print("   ✅ 연결 성공!")
        
        print("\n💰 현재 잔액 확인 중...")
        wallet = session.get_wallet_balance(accountType="UNIFIED")
        
        usdt_balance = 0
        for coin in wallet['result']['list'][0]['coin']:
            if coin['coin'] in ['USDT', 'USD']:
                usdt_balance = safe_float(coin.get('availableToWithdraw') or coin.get('equity'))
                break
        
        print(f"   - 사용 가능: {usdt_balance:,.2f} USDT")
        
        if usdt_balance < 100:
            print("   ❌ 잔액 부족!")
            return False
        
        print(f"\n📊 {symbol} 현재가 조회 중...")
        ticker = session.get_tickers(category=category, symbol=symbol)
        current_price = safe_float(ticker['result']['list'][0]['lastPrice'])
        print(f"   - 현재가: ${current_price:,.2f}")
        
        instruments = session.get_instruments_info(category=category, symbol=symbol)
        min_qty = safe_float(instruments['result']['list'][0]['lotSizeFilter']['minOrderQty'])
        print(f"   - 최소 수량: {min_qty} ETH")
        
        test_qty = min_qty
        test_value = test_qty * current_price
        
        print(f"\n🎯 테스트 주문 설정:")
        print(f"   - 수량: {test_qty} ETH")
        print(f"   - 예상 금액: ${test_value:,.2f}")
        
        response = input("\n⚠️  계속하려면 'y' 입력: ").strip().lower()
        if response != 'y':
            print("\n❌ 주문 취소됨")
            return False
        
        # ============================================================
        # Step 1: 매수 주문
        # ============================================================
        print("\n" + "=" * 60)
        print("📈 Step 1: 매수 주문 (LONG 진입)")
        print("=" * 60)
        
        # 제한가를 3% 높게 설정 (빠른 체결)
        buy_price = current_price * 1.03
        
        print(f"\n1️⃣ {test_qty} ETH 매수 주문 중...")
        print(f"   - 주문 가격: ${buy_price:,.2f} (현재가 +3%)")
        print(f"   - 주문 방식: Limit + IOC (즉시 체결)")
        
        buy_order = session.place_order(
            category=category,
            symbol=symbol,
            side="Buy",
            orderType="Limit",
            qty=str(test_qty),
            price=str(round(buy_price, 2)),
            timeInForce="IOC",  # 즉시 체결 또는 취소
            positionIdx=0
        )
        
        if buy_order['retCode'] != 0:
            print(f"   ❌ 매수 주문 실패: {buy_order['retMsg']}")
            return False
        
        order_id = buy_order['result']['orderId']
        print(f"   ✅ 매수 주문 접수!")
        print(f"   - 주문 ID: {order_id}")
        
        # 체결 확인
        print("\n2️⃣ 주문 체결 확인 중...")
        time.sleep(2)
        
        order_status = session.get_order_history(
            category=category,
            symbol=symbol,
            orderId=order_id
        )
        
        filled = False
        avg_price = current_price
        filled_qty = test_qty
        
        if order_status['result']['list']:
            order_info = order_status['result']['list'][0]
            order_state = order_info['orderStatus']
            filled_qty = safe_float(order_info['cumExecQty'])
            
            if order_state == 'Filled' and filled_qty > 0:
                filled = True
                avg_price = safe_float(order_info['avgPrice'])
                
                print(f"   ✅ 주문 체결 완료!")
                print(f"   - 체결 수량: {filled_qty} ETH")
                print(f"   - 평균 체결가: ${avg_price:,.2f}")
                print(f"   - 총 금액: ${filled_qty * avg_price:,.2f}")
            else:
                print(f"   ⚠️  주문 상태: {order_state}")
                print(f"   ⚠️  체결 수량: {filled_qty} ETH")
        
        if not filled or filled_qty == 0:
            print(f"\n   ❌ 주문이 체결되지 않았습니다")
            print(f"   💡 Testnet 유동성이 낮을 수 있습니다")
            print(f"   💡 BTC/USDT로 다시 시도해보세요")
            return False
        
        # ============================================================
        # Step 2: 포지션 확인
        # ============================================================
        print("\n" + "=" * 60)
        print("📊 Step 2: 포지션 확인")
        print("=" * 60)
        
        print("\n3️⃣ 현재 포지션 조회 중...")
        time.sleep(1)
        
        positions = session.get_positions(category=category, symbol=symbol)
        
        position_found = False
        if positions['retCode'] == 0:
            for pos in positions['result']['list']:
                size = safe_float(pos['size'])
                if size > 0:
                    position_found = True
                    side = pos['side']
                    entry_price = safe_float(pos['avgPrice'])
                    unrealized_pnl = safe_float(pos['unrealisedPnl'])
                    
                    print(f"   ✅ 포지션 확인!")
                    print(f"   - 방향: {side}")
                    print(f"   - 수량: {size} ETH")
                    print(f"   - 진입가: ${entry_price:,.2f}")
                    print(f"   - 미실현 손익: {unrealized_pnl:+,.2f} USDT")
                    
                    current_ticker = session.get_tickers(category=category, symbol=symbol)
                    now_price = safe_float(current_ticker['result']['list'][0]['lastPrice'])
                    price_change = ((now_price - entry_price) / entry_price) * 100
                    
                    print(f"   - 현재가: ${now_price:,.2f}")
                    print(f"   - 가격 변동: {price_change:+.2f}%")
                    break
        
        if not position_found:
            print("   ⚠️  포지션을 찾을 수 없습니다")
            return False
        
        # ============================================================
        # Step 3: 매도 주문
        # ============================================================
        print("\n" + "=" * 60)
        print("📉 Step 3: 매도 주문 (포지션 청산)")
        print("=" * 60)
        
        print(f"\n4️⃣ {filled_qty} ETH 매도 주문 중...")
        print("   ⏳ 3초 후 자동 청산...")
        time.sleep(3)
        
        current_ticker = session.get_tickers(category=category, symbol=symbol)
        current_sell_price = safe_float(current_ticker['result']['list'][0]['lastPrice'])
        
        # 제한가를 3% 낮게 설정 (빠른 체결)
        sell_price = current_sell_price * 0.97
        
        print(f"   - 주문 가격: ${sell_price:,.2f} (현재가 -3%)")
        
        sell_order = session.place_order(
            category=category,
            symbol=symbol,
            side="Sell",
            orderType="Limit",
            qty=str(filled_qty),
            price=str(round(sell_price, 2)),
            timeInForce="IOC",  # 즉시 체결
            positionIdx=0,
            reduceOnly=True
        )
        
        if sell_order['retCode'] != 0:
            print(f"   ❌ 매도 주문 실패: {sell_order['retMsg']}")
            print(f"   ⚠️  수동으로 청산해주세요!")
            return False
        
        sell_order_id = sell_order['result']['orderId']
        print(f"   ✅ 매도 주문 접수!")
        print(f"   - 주문 ID: {sell_order_id}")
        
        print("\n5️⃣ 청산 확인 중...")
        time.sleep(2)
        
        sell_order_status = session.get_order_history(
            category=category,
            symbol=symbol,
            orderId=sell_order_id
        )
        
        sell_avg_price = current_sell_price
        if sell_order_status['result']['list']:
            sell_info = sell_order_status['result']['list'][0]
            sell_state = sell_info['orderStatus']
            sell_filled_qty = safe_float(sell_info['cumExecQty'])
            
            if sell_state == 'Filled' and sell_filled_qty > 0:
                sell_avg_price = safe_float(sell_info['avgPrice'])
                print(f"   ✅ 청산 완료!")
                print(f"   - 체결 수량: {sell_filled_qty} ETH")
                print(f"   - 평균 체결가: ${sell_avg_price:,.2f}")
            else:
                print(f"   ⚠️  매도 상태: {sell_state}")
        
        # ============================================================
        # Step 4: 결과
        # ============================================================
        print("\n" + "=" * 60)
        print("💰 Step 4: 거래 결과")
        print("=" * 60)
        
        print("\n6️⃣ 최종 잔액 확인 중...")
        time.sleep(2)
        
        final_wallet = session.get_wallet_balance(accountType="UNIFIED")
        final_balance = 0
        for coin in final_wallet['result']['list'][0]['coin']:
            if coin['coin'] in ['USDT', 'USD']:
                final_balance = safe_float(coin.get('equity'))
                break
        
        profit_loss = final_balance - usdt_balance
        profit_loss_pct = (profit_loss / usdt_balance) * 100 if usdt_balance > 0 else 0
        
        print(f"\n📊 거래 요약:")
        print(f"   - 진입가: ${avg_price:,.2f}")
        print(f"   - 청산가: ${sell_avg_price:,.2f}")
        price_diff = sell_avg_price - avg_price
        price_diff_pct = (price_diff / avg_price) * 100
        print(f"   - 가격 차이: ${price_diff:+,.2f} ({price_diff_pct:+.2f}%)")
        print(f"   - 수량: {filled_qty} ETH")
        print(f"   - 시작 잔액: {usdt_balance:,.2f} USDT")
        print(f"   - 최종 잔액: {final_balance:,.2f} USDT")
        
        if profit_loss >= 0:
            print(f"   ✅ 손익: +{profit_loss:.2f} USDT ({profit_loss_pct:+.4f}%)")
        else:
            print(f"   ❌ 손익: {profit_loss:.2f} USDT ({profit_loss_pct:+.4f}%)")
        
        print("\n7️⃣ 최종 포지션 확인...")
        final_positions = session.get_positions(category=category, symbol=symbol)
        
        has_position = False
        if final_positions['retCode'] == 0:
            for pos in final_positions['result']['list']:
                if safe_float(pos['size']) > 0:
                    has_position = True
                    break
        
        if not has_position:
            print("   ✅ 모든 포지션 청산 완료!")
        else:
            print("   ⚠️  일부 포지션 남아있음")
        
        print("\n" + "=" * 60)
        print("✅ Phase 1.3 테스트 완료!")
        print("=" * 60)
        print(f"\n🎉 축하합니다!")
        print(f"\n📌 확인된 기능:")
        print(f"   ✅ 제한가 매수 주문")
        print(f"   ✅ 포지션 관리")
        print(f"   ✅ 제한가 매도 주문")
        print(f"   ✅ 손익 계산")
        print(f"\n🚀 다음: Phase 2 - 자동매매 전략 개발")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"📁 작업 폴더: {os.getcwd()}\n")
    test_order(use_testnet=True)