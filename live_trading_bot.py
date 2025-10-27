# live_trading_bot.py - 실시간 자동매매 봇 (Phase 2.0) - 실시간 로그

import sys
import io
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
import time
from datetime import datetime
import pandas as pd

# 로컬 모듈
from data_collector import DataCollector
from strategy import TradingStrategy
from order_manager import OrderManager

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
        
    def initialize(self):
        """초기화"""
        print("=" * 80, flush=True)
        print(f"Live Trading Bot - Phase 2.0", flush=True)
        print(f"환경: {self.env_name}", flush=True)
        print(f"심볼: {self.symbol}", flush=True)
        print(f"레버리지: {self.leverage}x", flush=True)
        print(f"체크 간격: {self.check_interval}초", flush=True)
        
        if self.dry_run:
            print(f"DRY RUN 모드 (실제 주문 안 함)", flush=True)
        else:
            print(f"실전 거래 모드", flush=True)
        
        print("=" * 80, flush=True)
        
        # 레버리지 설정
        if not self.dry_run:
            print("\n레버리지 설정 중...", flush=True)
            self.order_manager.set_leverage()
        
        # 잔액 확인
        print("\n잔액 확인 중...", flush=True)
        balance = self.order_manager.get_balance()
        print(f"   사용 가능: {balance:,.2f} USDT", flush=True)
        
        if balance < 10:
            print("   잔액이 부족합니다 (최소 10 USDT)", flush=True)
            return False
        
        # 현재 포지션 확인
        print("\n기존 포지션 확인 중...", flush=True)
        self.position = self.order_manager.get_position()
        
        if self.position:
            print(f"   기존 포지션 발견!", flush=True)
            print(f"   - 방향: {self.position['side']}", flush=True)
            print(f"   - 수량: {self.position['size']}", flush=True)
            print(f"   - 진입가: ${self.position['entry_price']:,.2f}", flush=True)
            print(f"   - 미실현 손익: {self.position['unrealized_pnl']:+,.2f} USDT", flush=True)
        else:
            print(f"   포지션 없음", flush=True)
        
        print("\n" + "=" * 80, flush=True)
        print("초기화 완료!", flush=True)
        print("=" * 80, flush=True)
        
        return True
    
    def check_signals(self):
        """시그널 체크"""
        try:
            # 데이터 수집
            print("   데이터 수집 중...", flush=True)
            data = self.data_collector.get_all_timeframes()
            
            if not all(df is not None for df in data.values()):
                print("   데이터 수집 실패", flush=True)
                return None
            
            print("   지표 계산 중...", flush=True)
            # 지표 계산
            df_1h = self.strategy.calculate_indicators(data['1h'])
            df_15m = self.strategy.calculate_indicators(data['15m'])
            df_5m = self.strategy.calculate_indicators(data['5m'])
            
            print("   시그널 분석 중...", flush=True)
            # 시그널 확인
            signal = self.strategy.check_entry_signal(df_1h, df_15m, df_5m)
            
            return signal
            
        except Exception as e:
            print(f"   시그널 체크 오류: {str(e)}", flush=True)
            return None
    
    def execute_entry(self, signal):
        """진입 주문 실행"""
        if self.dry_run:
            print("\n" + "=" * 80, flush=True)
            print("DRY RUN - 시그널 발견!", flush=True)
            print("=" * 80, flush=True)
            print(f"시간: {signal['timestamp']}", flush=True)
            print(f"진입가: ${signal['entry_price']:,.2f}", flush=True)
            print(f"TP1: ${signal['tp1_price']:,.2f} (+{signal['tp1_pct']:.1f}%)", flush=True)
            print(f"TP2: ${signal['tp2_price']:,.2f} (+{signal['tp2_pct']:.1f}%)", flush=True)
            print(f"SL: ${signal['sl_price']:,.2f} (-{signal['sl_pct']:.1f}%)", flush=True)
            print(f"품질: {signal['quality']}점", flush=True)
            print(f"변동성: {signal['vol_regime']} (ATR비율: {signal['atr_ratio']:.2f})", flush=True)
            print(f"시장: {signal['market_regime']}", flush=True)
            print("=" * 80, flush=True)
            return True
        
        # 실제 주문
        try:
            print("\n" + "=" * 80, flush=True)
            print("진입 주문 실행!", flush=True)
            print("=" * 80, flush=True)
            
            # 잔액 확인
            balance = self.order_manager.get_balance()
            print(f"사용 가능 잔액: {balance:,.2f} USDT", flush=True)
            
            # 포지션 크기 계산
            entry_price = signal['entry_price']
            print(f"\n포지션 크기 계산 중...", flush=True)
            quantity = self.order_manager.calculate_position_size(entry_price, balance, risk_pct=0.3)
            
            print(f"\n포지션 정보:", flush=True)
            print(f"   - 진입가: ${entry_price:,.2f}", flush=True)
            print(f"   - 수량: {quantity} {self.symbol.replace('USDT', '')}", flush=True)
            print(f"   - 포지션 가치: ${quantity * entry_price:,.2f}", flush=True)
            print(f"   - 레버리지: {self.leverage}x", flush=True)
            
            print(f"\n타겟:", flush=True)
            print(f"   - TP1: ${signal['tp1_price']:,.2f} (+{signal['tp1_pct']:.1f}%) [50% 청산]", flush=True)
            print(f"   - TP2: ${signal['tp2_price']:,.2f} (+{signal['tp2_pct']:.1f}%) [나머지 청산]", flush=True)
            print(f"   - SL: ${signal['sl_price']:,.2f} (-{signal['sl_pct']:.1f}%)", flush=True)
            
            print(f"\n시그널 정보:", flush=True)
            print(f"   - 품질: {signal['quality']}점", flush=True)
            print(f"   - 변동성: {signal['vol_regime']} (비율: {signal['atr_ratio']:.2f})", flush=True)
            print(f"   - 시장: {signal['market_regime']}", flush=True)
            
            # 시장가 매수
            print(f"\n주문 전송 중...", flush=True)
            result = self.order_manager.place_market_order('Buy', quantity)
            
            if result and result['status'] == 'Filled':
                self.position = {
                    'entry_price': result['price'],
                    'size': result['qty'],
                    'remaining_size': result['qty'],  # 남은 수량 추적
                    'tp1_price': signal['tp1_price'],
                    'tp2_price': signal['tp2_price'],
                    'sl_price': signal['sl_price'],
                    'trailing_stop': None,  # 트레일링 스톱 가격
                    'tp1_hit': False,  # TP1 도달 여부
                    'signal': signal,
                    'entry_time': datetime.now(),
                    'highest_price': result['price']  # 최고가 추적
                }
                
                print("\n진입 완료!", flush=True)
                print("=" * 80, flush=True)
                return True
            else:
                print("\n진입 실패!", flush=True)
                print("=" * 80, flush=True)
                return False
                
        except Exception as e:
            print(f"\n진입 오류: {str(e)}", flush=True)
            print("=" * 80, flush=True)
            return False
    
    def monitor_position(self):
        """포지션 모니터링 (백테스팅과 동일한 로직)"""
        if not self.position:
            return
        
        try:
            print("   현재가 조회 중...", flush=True)
            current_price = self.order_manager.get_current_price()
            
            if current_price == 0:
                print("   현재가 조회 실패", flush=True)
                return
            
            entry_price = self.position['entry_price']
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # 최고가 업데이트
            if current_price > self.position['highest_price']:
                self.position['highest_price'] = current_price
            
            print(f"   현재가: ${current_price:,.2f}", flush=True)
            print(f"   진입가: ${entry_price:,.2f}", flush=True)
            print(f"   최고가: ${self.position['highest_price']:,.2f}", flush=True)
            print(f"   손익: {pnl_pct:+.2f}%", flush=True)
            print(f"   남은 수량: {self.position['remaining_size']}", flush=True)
            
            should_close = False
            close_qty = None
            reason = ""
            
            # 1. TP1 체크 (50% 부분 청산)
            if not self.position['tp1_hit'] and current_price >= self.position['tp1_price']:
                should_close = True
                close_qty = self.position['remaining_size'] * 0.5
                reason = f"TP1 도달 - 50% 부분 청산"
                self.position['tp1_hit'] = True
            
            # 2. TP2 체크 (전량 청산)
            elif current_price >= self.position['tp2_price']:
                should_close = True
                close_qty = self.position['remaining_size']
                reason = f"TP2 도달 - 전량 청산"
            
            # 3. 트레일링 스톱 계산 및 체크
            elif self.position['tp1_hit']:
                # TP1 이후 트레일링 시작
                trailing_price = self.strategy.calculate_trailing_stop(
                    entry_price,
                    self.position['highest_price'],
                    self.position['signal']['vol_regime']
                )
                
                if trailing_price:
                    self.position['trailing_stop'] = trailing_price
                    print(f"   트레일링: ${trailing_price:,.2f}", flush=True)
                    
                    if current_price <= trailing_price:
                        should_close = True
                        close_qty = self.position['remaining_size']
                        reason = f"트레일링 스톱"
            
            # 4. 손절 체크
            if current_price <= self.position['sl_price']:
                should_close = True
                close_qty = self.position['remaining_size']
                reason = f"손절"
            
            # 5. 타임아웃 체크 (30일)
            holding_time = (datetime.now() - self.position['entry_time']).days
            if holding_time >= 30:
                should_close = True
                close_qty = self.position['remaining_size']
                reason = f"타임아웃 (30일 경과)"
            
            # 청산 실행
            if should_close and close_qty:
                print(f"\n청산 신호: {reason}", flush=True)
                print(f"   - 진입가: ${entry_price:,.2f}", flush=True)
                print(f"   - 현재가: ${current_price:,.2f}", flush=True)
                print(f"   - 청산 수량: {close_qty}", flush=True)
                print(f"   - 손익: {pnl_pct:+.2f}%", flush=True)
                
                if not self.dry_run:
                    print(f"\n청산 실행 중...", flush=True)
                    if self.order_manager.close_position(quantity=close_qty):
                        print(f"청산 완료!", flush=True)
                        
                        # 수량 업데이트
                        self.position['remaining_size'] -= close_qty
                        
                        # 전량 청산이면 포지션 제거
                        if self.position['remaining_size'] <= 0.001:
                            self.position = None
                else:
                    print(f"DRY RUN - 청산 시그널만 표시", flush=True)
            else:
                print(f"   청산 조건 미달", flush=True)
                    
        except Exception as e:
            print(f"모니터링 오류: {str(e)}", flush=True)
    
    def run(self):
        """메인 루프"""
        if not self.initialize():
            return
        
        print(f"\n봇 시작! (Ctrl+C로 중지)", flush=True)
        print(f"{self.check_interval}초마다 시그널 체크\n", flush=True)
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n{'='*80}", flush=True)
                print(f"사이클 #{cycle} - {now}", flush=True)
                print(f"{'='*80}", flush=True)
                
                # 포지션 있으면 모니터링
                if self.position:
                    print(f"포지션 모니터링 중...", flush=True)
                    self.monitor_position()
                
                # 포지션 없으면 시그널 체크
                else:
                    print(f"시그널 체크 중...", flush=True)
                    signal = self.check_signals()
                    
                    if signal:
                        print(f"\n진입 시그널 발견!", flush=True)
                        self.execute_entry(signal)
                    else:
                        print(f"   시그널 없음", flush=True)
                
                # 대기
                print(f"\n{self.check_interval}초 대기 중...", flush=True)
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n{'='*80}", flush=True)
            print(f"봇 중지 요청", flush=True)
            print(f"{'='*80}", flush=True)
            
            # 포지션 있으면 알림
            if self.position:
                print(f"\n포지션이 남아있습니다!", flush=True)
                pos = self.order_manager.get_position()
                if pos:
                    print(f"   - 방향: {pos['side']}", flush=True)
                    print(f"   - 수량: {pos['size']}", flush=True)
                    print(f"   - 진입가: ${pos['entry_price']:,.2f}", flush=True)
                    print(f"   - 미실현 손익: {pos['unrealized_pnl']:+,.2f} USDT", flush=True)
            
            print(f"\n봇 종료", flush=True)

if __name__ == "__main__":
    # DRY RUN 모드 (시그널만 표시)
    bot = LiveTradingBot(testnet=False, dry_run=True)
    
    # 실제 거래 모드
    #bot = LiveTradingBot(testnet=True, dry_run=False)
    
    bot.run()