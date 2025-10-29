# order_manager.py - 주문 실행 및 포지션 관리 (수량 포맷 수정)

from pybit.unified_trading import HTTP
import time
from datetime import datetime

class OrderManager:
    """주문 실행 및 포지션 관리"""
    
    def __init__(self, session, symbol='ETHUSDT', leverage=2):
        self.session = session
        self.symbol = symbol
        self.leverage = leverage
        self.category = 'linear'
        self.position = None
        
    def set_leverage(self):
        """레버리지 설정"""
        try:
            result = self.session.set_leverage(
                category=self.category,
                symbol=self.symbol,
                buyLeverage=str(self.leverage),
                sellLeverage=str(self.leverage)
            )
            
            if result['retCode'] == 0:
                print(f"   레버리지 {self.leverage}x 설정 완료")
                return True
            elif result['retCode'] == 110043:
                print(f"   레버리지 {self.leverage}x (이미 설정됨)")
                return True
            else:
                print(f"   레버리지 설정 실패: {result['retMsg']}")
                return False
                
        except Exception as e:
            if '110043' in str(e):
                print(f"   레버리지 {self.leverage}x (이미 설정됨)")
                return True
            print(f"   레버리지 설정 오류: {str(e)}")
            return False
    
    def get_balance(self):
        """잔액 조회"""
        try:
            result = self.session.get_wallet_balance(accountType="UNIFIED")
            
            if result['retCode'] != 0:
                return 0
            
            for coin in result['result']['list'][0]['coin']:
                if coin['coin'] in ['USDT', 'USD']:
                    equity = float(coin.get('equity') or 0)
                    available = float(coin.get('availableToWithdraw') or coin.get('equity') or 0)
                    return available
            
            return 0
            
        except Exception as e:
            print(f"   잔액 조회 오류: {str(e)}")
            return 0
    
    def get_current_price(self):
        """현재가 조회"""
        try:
            result = self.session.get_tickers(
                category=self.category,
                symbol=self.symbol
            )
            
            if result['retCode'] == 0 and result['result']['list']:
                return float(result['result']['list'][0]['lastPrice'])
            
            return 0
            
        except Exception as e:
            print(f"   현재가 조회 오류: {str(e)}")
            return 0
    
    def get_instrument_info(self):
        """상품 정보 조회 (최소 수량, 소수점 자리)"""
        try:
            result = self.session.get_instruments_info(
                category=self.category,
                symbol=self.symbol
            )
            
            if result['retCode'] == 0 and result['result']['list']:
                info = result['result']['list'][0]
                lot_filter = info['lotSizeFilter']
                
                min_qty = float(lot_filter['minOrderQty'])
                qty_step = float(lot_filter['qtyStep'])
                
                # 소수점 자리 계산
                if '.' in str(qty_step):
                    precision = len(str(qty_step).split('.')[1].rstrip('0'))
                else:
                    precision = 0
                
                return {
                    'min_qty': min_qty,
                    'qty_step': qty_step,
                    'precision': precision
                }
            
            return {'min_qty': 0.001, 'qty_step': 0.001, 'precision': 3}
            
        except Exception as e:
            print(f"   상품 정보 조회 실패: {str(e)}")
            return {'min_qty': 0.001, 'qty_step': 0.001, 'precision': 3}
    
    def calculate_position_size(self, entry_price, balance, risk_pct=0.3):
        """
        포지션 크기 계산
        
        Args:
            entry_price: 진입 가격
            balance: 사용 가능 잔액
            risk_pct: 최대 사용 비율 (기본 30%)
        """
        # 상품 정보
        info = self.get_instrument_info()
        
        # 사용 가능 금액
        usable = balance * risk_pct
        
        # 레버리지 적용
        position_value = usable * self.leverage
        
        # 수량 계산
        quantity = position_value / entry_price
        
        # 소수점 자리 맞춤
        precision = info['precision']
        quantity_rounded = round(quantity, precision)
        
        # 최소 수량 체크
        if quantity_rounded < info['min_qty']:
            quantity_rounded = info['min_qty']
        
        print(f"   수량 조정:")
        print(f"      원본: {quantity:.10f}")
        print(f"      반올림: {quantity_rounded} (소수점 {precision}자리)")
        print(f"      최소 수량: {info['min_qty']}")
        
        return quantity_rounded
    
    def place_market_order(self, side, quantity, reduce_only=False):
        """
        시장가 주문
        
        Args:
            side: 'Buy' | 'Sell'
            quantity: 주문 수량
            reduce_only: 포지션 청산 전용
        """
        try:
            # 수량 포맷 조정
            info = self.get_instrument_info()
            qty_formatted = round(quantity, info['precision'])
            
            print(f"\n Buy 주문 전송 중...")
            print(f"   - 수량: {qty_formatted}")
            print(f"   - 타입: Market")
            
            order = self.session.place_order(
                category=self.category,
                symbol=self.symbol,
                side=side,
                orderType="Market",
                qty=str(qty_formatted),
                timeInForce="IOC",
                positionIdx=0,
                reduceOnly=reduce_only
            )
            
            if order['retCode'] != 0:
                print(f"   주문 실패: {order['retMsg']}")
                return None
            
            order_id = order['result']['orderId']
            print(f"   주문 접수: {order_id}")
            
            # 체결 확인
            time.sleep(2)
            order_info = self.check_order(order_id)
            
            return order_info
            
        except Exception as e:
            print(f"   주문 오류: {str(e)}")
            return None
    
    def place_limit_order(self, side, quantity, price, reduce_only=False):
        """
        지정가 주문
        
        Args:
            side: 'Buy' | 'Sell'
            quantity: 주문 수량
            price: 지정 가격
            reduce_only: 포지션 청산 전용
        """
        try:
            # 수량 포맷 조정
            info = self.get_instrument_info()
            qty_formatted = round(quantity, info['precision'])
            
            print(f"\n {side} 지정가 주문 전송 중...")
            print(f"   - 수량: {qty_formatted}")
            print(f"   - 가격: ${price:,.2f}")
            
            order = self.session.place_order(
                category=self.category,
                symbol=self.symbol,
                side=side,
                orderType="Limit",
                qty=str(qty_formatted),
                price=str(round(price, 2)),
                timeInForce="GTC",
                positionIdx=0,
                reduceOnly=reduce_only
            )
            
            if order['retCode'] != 0:
                print(f"   주문 실패: {order['retMsg']}")
                return None
            
            order_id = order['result']['orderId']
            print(f"   주문 접수: {order_id}")
            
            return {'orderId': order_id, 'status': 'Pending'}
            
        except Exception as e:
            print(f"   주문 오류: {str(e)}")
            return None
    
    def check_order(self, order_id):
        """주문 상태 확인"""
        try:
            result = self.session.get_order_history(
                category=self.category,
                symbol=self.symbol,
                orderId=order_id
            )
            
            if result['retCode'] == 0 and result['result']['list']:
                order = result['result']['list'][0]
                
                status = order['orderStatus']
                filled_qty = float(order.get('cumExecQty', 0))
                avg_price = float(order.get('avgPrice', 0))
                
                if status == 'Filled' and filled_qty > 0:
                    print(f"   체결 완료!")
                    print(f"   - 수량: {filled_qty}")
                    print(f"   - 평균가: ${avg_price:,.2f}")
                    
                    return {
                        'orderId': order_id,
                        'status': 'Filled',
                        'qty': filled_qty,
                        'price': avg_price
                    }
                else:
                    print(f"   주문 상태: {status}")
                    return {
                        'orderId': order_id,
                        'status': status,
                        'qty': filled_qty,
                        'price': avg_price
                    }
            
            return None
            
        except Exception as e:
            print(f"   주문 확인 오류: {str(e)}")
            return None
    
    def get_position(self):
        """현재 포지션 조회"""
        try:
            result = self.session.get_positions(
                category=self.category,
                symbol=self.symbol
            )
            
            if result['retCode'] != 0:
                return None
            
            for pos in result['result']['list']:
                size = float(pos.get('size', 0))
                if size > 0:
                    return {
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'size': size,
                        'entry_price': float(pos['avgPrice']),
                        'unrealized_pnl': float(pos.get('unrealisedPnl', 0)),
                        'leverage': float(pos.get('leverage', 0))
                    }
            
            return None
            
        except Exception as e:
            print(f"   포지션 조회 오류: {str(e)}")
            return None
    
    def close_position(self, quantity=None):
        """포지션 청산"""
        try:
            position = self.get_position()
            
            if not position:
                print("   청산할 포지션이 없습니다")
                return False
            
            qty = quantity if quantity else position['size']
            side = 'Sell' if position['side'] == 'Buy' else 'Buy'
            
            print(f"\n 포지션 청산 중...")
            print(f"   - 방향: {position['side']}")
            print(f"   - 수량: {qty}")
            
            result = self.place_market_order(side, qty, reduce_only=True)
            
            if result and result['status'] == 'Filled':
                print(f"   청산 완료!")
                return True
            
            return False
            
        except Exception as e:
            print(f"   청산 오류: {str(e)}")
            return False
    
    def cancel_all_orders(self):
        """모든 미체결 주문 취소"""
        try:
            result = self.session.cancel_all_orders(
                category=self.category,
                symbol=self.symbol
            )
            
            if result['retCode'] == 0:
                print("   모든 미체결 주문 취소 완료")
                return True
            
            return False
            
        except Exception as e:
            print(f"   주문 취소 오류: {str(e)}")
            return False