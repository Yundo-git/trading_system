# live_trading_bot.py - 실시간 자동매매 봇 (Phase 2.0 최종 완성판)
# ✨ 개선사항:
# - 현재가 기준 수량 계산
# - 슬리피지 체크 (1.5% 제한)
# - 상세한 청산 로그 (시간, 금액, 수익률)

import sys
import io
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import pandas as pd

import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
ROOT_DIR = Path(__file__).parent.parent

# 상대 경로로 임포트
import sys
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 로컬 모듈 - 절대 경로로 임포트
from data.data_collector import DataCollector
from trading.strategy import TradingStrategy
from trading.order_manager import OrderManager

# Windows 콘솔 인코딩 + 버퍼링 비활성화
os.environ['PYTHONUNBUFFERED'] = '1'
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

class LiveTradingBot:
    """실시간 자동매매 봇"""
    
    def __init__(self, testnet=True, dry_run=False):
        """
        Args:
            testnet: True면 Testnet, False면 Mainnet
            dry_run: True면 실제 주문 안 함 (시그널만 표시)
        """
        self.testnet = testnet
        self.dry_run = dry_run
        
        # 환경 변수 로드
        load_dotenv()
        
        # API 키
        if testnet:
            api_key = os.getenv('BYBIT_TESTNET_API_KEY')
            api_secret = os.getenv('BYBIT_TESTNET_API_SECRET')
            self.env_name = "TESTNET"
        else:
            api_key = os.getenv('BYBIT_API_KEY')
            api_secret = os.getenv('BYBIT_API_SECRET')
            self.env_name = "MAINNET"
        
        # 거래 설정
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTCUSDT')
        self.leverage = int(os.getenv('LEVERAGE', '2'))
        self.check_interval = 300  # 5분마다 체크
        self.max_slippage = 1.5  # 최대 슬리피지 1.5%
        
        # Bybit 세션
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret,
            recv_window=60000
        )
        
        # 모듈 초기화
        self.data_collector = DataCollector(self.session, self.symbol, testnet)
        self.strategy = TradingStrategy()
        self.order_manager = OrderManager(self.session, self.symbol, self.leverage)
        
        # 상태
        self.position = None
        self.last_signal_time = None
        
        # 통계
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0.0
        
    def initialize(self):
        """초기화"""
        print("=" * 80, flush=True)
        print(f"🤖 Live Trading Bot - Phase 2.0 (최종 완성판)", flush=True)
        print(f"환경: {self.env_name}", flush=True)
        print(f"심볼: {self.symbol}", flush=True)
        print(f"레버리지: {self.leverage}x", flush=True)
        print(f"체크 간격: {self.check_interval}초", flush=True)
        print(f"최대 슬리피지: {self.max_slippage}%", flush=True)
        
        if self.dry_run:
            print(f"🔍 DRY RUN 모드 (실제 주문 안 함)", flush=True)
        else:
            print(f"⚠️  실전 거래 모드", flush=True)
        
        print("=" * 80, flush=True)
        
        # 레버리지 설정
        if not self.dry_run:
            print("\n⚙️  레버리지 설정 중...", flush=True)
            self.order_manager.set_leverage()
        
        # 잔액 확인
        print("\n💰 잔액 확인 중...", flush=True)
        balance = self.order_manager.get_balance()
        print(f"   사용 가능: {balance:,.2f} USDT", flush=True)
        
        if balance < 10:
            print("   ❌ 잔액이 부족합니다 (최소 10 USDT)", flush=True)
            return False
        
        # 현재 포지션 확인
        print("\n📊 기존 포지션 확인 중...", flush=True)
        self.position = self.order_manager.get_position()
        
        if self.position:
            print(f"   ⚠️  기존 포지션 발견!", flush=True)
            print(f"   - 방향: {self.position['side']}", flush=True)
            print(f"   - 수량: {self.position['size']}", flush=True)
            print(f"   - 진입가: ${self.position['entry_price']:,.2f}", flush=True)
            print(f"   - 미실현 손익: {self.position['unrealized_pnl']:+,.2f} USDT", flush=True)
        else:
            print(f"   ✅ 포지션 없음", flush=True)
        
        print("\n" + "=" * 80, flush=True)
        print("✅ 초기화 완료!", flush=True)
        print("=" * 80, flush=True)
        
        return True
    
    def check_signals(self):
        """시그널 체크"""
        try:
            # 데이터 수집
            print("   📡 데이터 수집 중...", flush=True)
            data = self.data_collector.get_all_timeframes()
            
            if not all(df is not None for df in data.values()):
                print("   ❌ 데이터 수집 실패", flush=True)
                return None
            
            print("   🔍 지표 계산 중...", flush=True)
            # 지표 계산
            df_1h = self.strategy.calculate_indicators(data['1h'])
            df_15m = self.strategy.calculate_indicators(data['15m'])
            df_5m = self.strategy.calculate_indicators(data['5m'])
            
            print("   📈 시그널 분석 중...", flush=True)
            # 시그널 확인
            signal = self.strategy.check_entry_signal(df_1h, df_15m, df_5m)
            
            return signal
            
        except Exception as e:
            print(f"   ❌ 시그널 체크 오류: {str(e)}", flush=True)
            return None
    
    def execute_entry(self, signal):
        """진입 주문 실행 - 현재가 기준 + 슬리피지 체크"""
        try:
            # Step 1: 현재가 조회
            print("\n   💰 현재가 조회 중...", flush=True)
            current_price = self.order_manager.get_current_price()
            
            if current_price == 0:
                print("   ❌ 현재가 조회 실패", flush=True)
                return False
            
            signal_price = signal['entry_price']
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Step 2: 슬리피지 체크 (안전장치)
            slippage_pct = abs(current_price - signal_price) / signal_price * 100
            
            print(f"\n   📊 가격 분석:", flush=True)
            print(f"      시그널가: ${signal_price:,.2f} (1시간봉 종가)", flush=True)
            print(f"      현재가: ${current_price:,.2f}", flush=True)
            print(f"      슬리피지: {slippage_pct:.2f}%", flush=True)
            
            if slippage_pct > self.max_slippage:
                print(f"\n   ⚠️  슬리피지 과다: {slippage_pct:.2f}% > {self.max_slippage}%", flush=True)
                print(f"   ❌ 주문 취소 (가격 변동이 너무 큼)", flush=True)
                print(f"   💡 다음 사이클을 기다립니다", flush=True)
                return False
            
            if self.dry_run:
                # DRY RUN 모드: 현재가 기준으로 시뮬레이션
                tp1_pct = signal['tp1_pct'] / 100
                tp2_pct = signal['tp2_pct'] / 100
                sl_pct = signal['sl_pct'] / 100
                
                current_tp1 = current_price * (1 + tp1_pct)
                current_tp2 = current_price * (1 + tp2_pct)
                current_sl = current_price * (1 - sl_pct)
                
                print("\n" + "=" * 80, flush=True)
                print("🔍 DRY RUN - 진입 시그널!", flush=True)
                print("=" * 80, flush=True)
                print(f"⏰ 현재 시간: {current_time}", flush=True)
                print(f"💰 현재 진입가: ${current_price:,.2f}", flush=True)
                print(f"🎯 TP1: ${current_tp1:,.2f} (+{signal['tp1_pct']:.1f}%) [50% 청산]", flush=True)
                print(f"🎯 TP2: ${current_tp2:,.2f} (+{signal['tp2_pct']:.1f}%) [나머지 청산]", flush=True)
                print(f"🛑 SL: ${current_sl:,.2f} (-{signal['sl_pct']:.1f}%)", flush=True)
                print(f"⭐ 품질: {signal['quality']}점", flush=True)
                print(f"🌡️  변동성: {signal['vol_regime']} (ATR비율: {signal['atr_ratio']:.2f})", flush=True)
                print(f"📊 시장: {signal['market_regime']}", flush=True)
                print(f"📉 슬리피지: {slippage_pct:.2f}%", flush=True)
                print("=" * 80, flush=True)
                return True
            
            # Step 3: 실제 주문 실행
            print("\n" + "=" * 80, flush=True)
            print("🚀 진입 주문 실행!", flush=True)
            print("=" * 80, flush=True)
            
            # 잔액 확인
            balance = self.order_manager.get_balance()
            print(f"💰 사용 가능 잔액: {balance:,.2f} USDT", flush=True)
            
            # Step 4: 현재가 기준으로 수량 계산 (정확함!)
            print(f"\n📊 포지션 크기 계산 중 (현재가 기준)...", flush=True)
            quantity = self.order_manager.calculate_position_size(
                current_price,  # ⭐ 현재가 기준!
                balance,
                risk_pct=0.3
            )
            
            print(f"\n📋 주문 정보:", flush=True)
            print(f"   - 기준가: ${current_price:,.2f} (현재가)", flush=True)
            print(f"   - 수량: {quantity} {self.symbol.replace('USDT', '')}", flush=True)
            print(f"   - 포지션 가치: ${quantity * current_price:,.2f}", flush=True)
            print(f"   - 레버리지: {self.leverage}x", flush=True)
            print(f"   - 슬리피지: {slippage_pct:.2f}%", flush=True)
            
            print(f"\n🎯 예상 타겟:", flush=True)
            print(f"   - TP1: +{signal['tp1_pct']:.1f}% [50% 청산]", flush=True)
            print(f"   - TP2: +{signal['tp2_pct']:.1f}% [나머지 청산]", flush=True)
            print(f"   - SL: -{signal['sl_pct']:.1f}%", flush=True)
            
            print(f"\n📊 시그널 정보:", flush=True)
            print(f"   - 품질: {signal['quality']}점", flush=True)
            print(f"   - 변동성: {signal['vol_regime']} (비율: {signal['atr_ratio']:.2f})", flush=True)
            print(f"   - 시장: {signal['market_regime']}", flush=True)
            
            # Step 5: 시장가 매수 (빠른 체결)
            print(f"\n📤 시장가 매수 주문 전송 중...", flush=True)
            result = self.order_manager.place_market_order('Buy', quantity)
            
            if not result or result['status'] != 'Filled':
                print("\n❌ 진입 실패!", flush=True)
                print("=" * 80, flush=True)
                return False
            
            # Step 6: 실제 체결가 기준으로 TP/SL 재계산
            actual_entry = result['price']
            tp1_pct = signal['tp1_pct'] / 100
            tp2_pct = signal['tp2_pct'] / 100
            sl_pct = signal['sl_pct'] / 100
            
            actual_tp1 = actual_entry * (1 + tp1_pct)
            actual_tp2 = actual_entry * (1 + tp2_pct)
            actual_sl = actual_entry * (1 - sl_pct)
            
            # 실제 슬리피지 계산
            actual_slippage = ((actual_entry - signal_price) / signal_price) * 100
            
            print(f"\n🔄 실제 체결 정보:", flush=True)
            print(f"   - 체결가: ${actual_entry:,.2f}", flush=True)
            print(f"   - 체결 수량: {result['qty']} {self.symbol.replace('USDT', '')}", flush=True)
            print(f"   - 실제 슬리피지: {actual_slippage:+.2f}%", flush=True)
            
            print(f"\n🎯 확정 타겟 (체결가 기준):", flush=True)
            print(f"   - TP1: ${actual_tp1:,.2f} (+{signal['tp1_pct']:.1f}%)", flush=True)
            print(f"   - TP2: ${actual_tp2:,.2f} (+{signal['tp2_pct']:.1f}%)", flush=True)
            print(f"   - SL: ${actual_sl:,.2f} (-{signal['sl_pct']:.1f}%)", flush=True)
            
            # 포지션 정보 저장
            self.position = {
                'entry_price': actual_entry,
                'entry_time': datetime.now(),
                'size': result['qty'],
                'remaining_size': result['qty'],
                'tp1_price': actual_tp1,
                'tp2_price': actual_tp2,
                'sl_price': actual_sl,
                'trailing_stop': None,
                'tp1_hit': False,
                'signal': signal,
                'highest_price': actual_entry,
                'initial_balance': balance
            }
            
            print("\n✅ 진입 완료!", flush=True)
            print("=" * 80, flush=True)
            return True
            
        except Exception as e:
            print(f"\n❌ 진입 오류: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            print("=" * 80, flush=True)
            return False
    
    def monitor_position(self):
        """포지션 모니터링 + 상세 청산 로그"""
        if not self.position:
            return
        
        try:
            print("   📊 현재가 조회 중...", flush=True)
            current_price = self.order_manager.get_current_price()
            
            if current_price == 0:
                print("   ❌ 현재가 조회 실패", flush=True)
                return
            
            entry_price = self.position['entry_price']
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # 최고가 업데이트
            if current_price > self.position['highest_price']:
                self.position['highest_price'] = current_price
            
            # 보유 시간 계산
            holding_time = datetime.now() - self.position['entry_time']
            hours = holding_time.total_seconds() / 3600
            
            print(f"   💰 현재가: ${current_price:,.2f}", flush=True)
            print(f"   📍 진입가: ${entry_price:,.2f}", flush=True)
            print(f"   📈 최고가: ${self.position['highest_price']:,.2f}", flush=True)
            print(f"   💵 손익: {pnl_pct:+.2f}%", flush=True)
            print(f"   📦 남은 수량: {self.position['remaining_size']}", flush=True)
            print(f"   ⏱️  보유 시간: {hours:.1f}시간", flush=True)
            
            should_close = False
            close_qty = None
            reason = ""
            exit_type = ""
            
            # 1. TP1 체크 (50% 부분 청산)
            if not self.position['tp1_hit'] and current_price >= self.position['tp1_price']:
                should_close = True
                close_qty = self.position['remaining_size'] * 0.5
                reason = f"🎯 TP1 도달"
                exit_type = "TP1"
                self.position['tp1_hit'] = True
            
            # 2. TP2 체크 (전량 청산)
            elif current_price >= self.position['tp2_price']:
                should_close = True
                close_qty = self.position['remaining_size']
                reason = f"🎯 TP2 도달"
                exit_type = "TP2"
            
            # 3. 트레일링 스톱 계산 및 체크
            elif self.position['tp1_hit']:
                trailing_price = self.strategy.calculate_trailing_stop(
                    entry_price,
                    self.position['highest_price'],
                    self.position['signal']['vol_regime']
                )
                
                if trailing_price:
                    self.position['trailing_stop'] = trailing_price
                    print(f"   🔄 트레일링: ${trailing_price:,.2f}", flush=True)
                    
                    if current_price <= trailing_price:
                        should_close = True
                        close_qty = self.position['remaining_size']
                        reason = f"🔄 트레일링 스톱"
                        exit_type = "TRAILING"
            
            # 4. 손절 체크
            if current_price <= self.position['sl_price']:
                should_close = True
                close_qty = self.position['remaining_size']
                reason = f"🛑 손절"
                exit_type = "SL"
            
            # 5. 타임아웃 체크 (30일)
            holding_days = holding_time.days
            if holding_days >= 30:
                should_close = True
                close_qty = self.position['remaining_size']
                reason = f"⏰ 타임아웃 (30일 경과)"
                exit_type = "TIMEOUT"
            
            # 청산 실행
            if should_close and close_qty:
                self._execute_exit(
                    reason=reason,
                    exit_type=exit_type,
                    close_qty=close_qty,
                    current_price=current_price,
                    holding_time=holding_time
                )
            else:
                print(f"   ⏳ 청산 조건 미달", flush=True)
                    
        except Exception as e:
            print(f"❌ 모니터링 오류: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
    
    def _execute_exit(self, reason, exit_type, close_qty, current_price, holding_time):
        """청산 실행 + 상세 로그"""
        entry_price = self.position['entry_price']
        entry_time = self.position['entry_time']
        exit_time = datetime.now()
        
        # 손익 계산
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        position_value = close_qty * entry_price
        pnl_amount = close_qty * (current_price - entry_price)
        
        # 부분 청산인지 전량 청산인지
        is_partial = close_qty < self.position['size']
        close_pct = (close_qty / self.position['size']) * 100
        
        print(f"\n{'='*80}", flush=True)
        print(f"📤 청산 신호: {reason}", flush=True)
        print(f"{'='*80}", flush=True)
        
        print(f"\n⏰ 시간 정보:", flush=True)
        print(f"   - 진입 시간: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"   - 청산 시간: {exit_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"   - 보유 기간: {holding_time.days}일 {holding_time.seconds//3600}시간 {(holding_time.seconds%3600)//60}분", flush=True)
        
        print(f"\n💰 가격 정보:", flush=True)
        print(f"   - 진입가: ${entry_price:,.2f}", flush=True)
        print(f"   - 청산가: ${current_price:,.2f}", flush=True)
        print(f"   - 최고가: ${self.position['highest_price']:,.2f}", flush=True)
        print(f"   - 가격 변동: {pnl_pct:+.2f}%", flush=True)
        
        print(f"\n📦 수량 정보:", flush=True)
        print(f"   - 전체 수량: {self.position['size']}", flush=True)
        print(f"   - 청산 수량: {close_qty} ({close_pct:.0f}%)", flush=True)
        print(f"   - 청산 유형: {'부분 청산' if is_partial else '전량 청산'}", flush=True)
        
        print(f"\n💵 손익 정보:", flush=True)
        print(f"   - 포지션 가치: ${position_value:,.2f}", flush=True)
        if pnl_amount >= 0:
            print(f"   - 실현 손익: +${pnl_amount:,.2f} (+{pnl_pct:.2f}%) ✅", flush=True)
        else:
            print(f"   - 실현 손익: ${pnl_amount:,.2f} ({pnl_pct:.2f}%) ❌", flush=True)
        
        # 실제 청산 실행
        if not self.dry_run:
            print(f"\n📤 청산 주문 전송 중...", flush=True)
            success = self.order_manager.close_position(quantity=close_qty)
            
            if success:
                print(f"✅ 청산 완료!", flush=True)
                
                # 통계 업데이트
                self.total_trades += 1
                if pnl_amount > 0:
                    self.winning_trades += 1
                self.total_profit += pnl_amount
                
                # 잔액 조회
                final_balance = self.order_manager.get_balance()
                initial_balance = self.position.get('initial_balance', 0)
                balance_change = final_balance - initial_balance
                
                print(f"\n💰 잔액 변동:", flush=True)
                print(f"   - 진입 전: ${initial_balance:,.2f}", flush=True)
                print(f"   - 청산 후: ${final_balance:,.2f}", flush=True)
                if balance_change >= 0:
                    print(f"   - 변동: +${balance_change:,.2f} ✅", flush=True)
                else:
                    print(f"   - 변동: ${balance_change:,.2f} ❌", flush=True)
                
                # 수량 업데이트
                self.position['remaining_size'] -= close_qty
                
                # 전량 청산이면 포지션 제거 + 통계 출력
                if self.position['remaining_size'] <= 0.001:
                    print(f"\n📊 거래 통계:", flush=True)
                    print(f"   - 총 거래: {self.total_trades}회", flush=True)
                    print(f"   - 승률: {self.winning_trades}/{self.total_trades} ({(self.winning_trades/self.total_trades*100) if self.total_trades > 0 else 0:.1f}%)", flush=True)
                    print(f"   - 누적 손익: ${self.total_profit:,.2f}", flush=True)
                    
                    self.position = None
                    print(f"\n✅ 모든 포지션 청산 완료", flush=True)
            else:
                print(f"❌ 청산 실패!", flush=True)
        else:
            print(f"\n🔍 DRY RUN - 청산 시뮬레이션", flush=True)
            print(f"   (실제로는 주문이 전송되지 않습니다)", flush=True)
        
        print(f"{'='*80}", flush=True)
    
    def run(self):
        """메인 루프"""
        if not self.initialize():
            return
        
        print(f"\n🚀 봇 시작! (Ctrl+C로 중지)", flush=True)
        print(f"⏰ {self.check_interval}초마다 시그널 체크\n", flush=True)
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n{'='*80}", flush=True)
                print(f"🔄 사이클 #{cycle} - {now}", flush=True)
                print(f"{'='*80}", flush=True)
                
                # 포지션 있으면 모니터링
                if self.position:
                    print(f"📊 포지션 모니터링 중...", flush=True)
                    self.monitor_position()
                
                # 포지션 없으면 시그널 체크
                else:
                    print(f"🔍 시그널 체크 중...", flush=True)
                    signal = self.check_signals()
                    
                    if signal:
                        print(f"\n✅ 진입 시그널 발견!", flush=True)
                        self.execute_entry(signal)
                    else:
                        print(f"   ⏳ 시그널 없음", flush=True)
                
                # 대기
                print(f"\n⏰ {self.check_interval}초 대기 중...", flush=True)
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n{'='*80}", flush=True)
            print(f"⏸️  봇 중지 요청", flush=True)
            print(f"{'='*80}", flush=True)
            
            # 통계 출력
            if self.total_trades > 0:
                print(f"\n📊 최종 거래 통계:", flush=True)
                print(f"   - 총 거래: {self.total_trades}회", flush=True)
                print(f"   - 승률: {self.winning_trades}/{self.total_trades} ({(self.winning_trades/self.total_trades*100):.1f}%)", flush=True)
                print(f"   - 누적 손익: ${self.total_profit:,.2f}", flush=True)
            
            # 포지션 있으면 알림
            if self.position:
                print(f"\n⚠️  포지션이 남아있습니다!", flush=True)
                pos = self.order_manager.get_position()
                if pos:
                    print(f"   - 방향: {pos['side']}", flush=True)
                    print(f"   - 수량: {pos['size']}", flush=True)
                    print(f"   - 진입가: ${pos['entry_price']:,.2f}", flush=True)
                    print(f"   - 미실현 손익: {pos['unrealized_pnl']:+,.2f} USDT", flush=True)
            
            print(f"\n👋 봇 종료", flush=True)

if __name__ == "__main__":
    # DRY RUN 모드 (시그널만 표시)
    bot = LiveTradingBot(testnet=False, dry_run=True)
    
    # 실제 거래 모드
    #bot = LiveTradingBot(testnet=True, dry_run=False)
    
    bot.run()