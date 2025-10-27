# data_collector.py - 실시간 데이터 수집

from pybit.unified_trading import HTTP
import pandas as pd
from datetime import datetime, timedelta
import time

class DataCollector:
    """Bybit에서 실시간 캔들 데이터 수집"""
    
    def __init__(self, session, symbol='BTCUSDT', testnet=True):
        self.session = session
        self.symbol = symbol
        self.testnet = testnet
        self.category = 'linear'
        
    def fetch_klines(self, interval='60', limit=500):
        """
        캔들 데이터 가져오기
        
        Args:
            interval: '1' | '5' | '15' | '60' | '240' (분 단위)
            limit: 최대 1000개
        """
        try:
            result = self.session.get_kline(
                category=self.category,
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            
            if result['retCode'] != 0:
                print(f"❌ 캔들 데이터 가져오기 실패: {result['retMsg']}")
                return None
            
            # 데이터 변환
            klines = result['result']['list']
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # 타입 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 시간 순 정렬
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"❌ 오류: {str(e)}")
            return None
    
    def get_all_timeframes(self):
        """
        모든 시간프레임 데이터 가져오기
        
        Returns:
            dict: {'1h': df, '15m': df, '5m': df}
        """
        print(f"📊 {self.symbol} 데이터 수집 중...")
        
        data = {}
        
        # 1시간
        print("   ⏰ 1h 캔들...")
        data['1h'] = self.fetch_klines(interval='60', limit=500)
        time.sleep(0.5)
        
        # 15분
        print("   ⏰ 15m 캔들...")
        data['15m'] = self.fetch_klines(interval='15', limit=500)
        time.sleep(0.5)
        
        # 5분
        print("   ⏰ 5m 캔들...")
        data['5m'] = self.fetch_klines(interval='5', limit=500)
        
        success_count = sum(1 for df in data.values() if df is not None)
        print(f"   ✅ {success_count}/3 성공")
        
        return data