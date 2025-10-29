"""
Data collection module for the trading system.
Handles fetching and processing market data.
"""
from typing import Dict, Optional, Union
import pandas as pd
from pybit.unified_trading import HTTP

class DataCollector:
    """Class for collecting and processing trading data."""
    
    def __init__(self, session: HTTP, symbol: str = 'BTCUSDT', testnet: bool = True):
        """
        Initialize the DataCollector.
        
        Args:
            session: Bybit HTTP session
            symbol: Trading symbol (e.g., 'BTCUSDT')
            testnet: Whether to use testnet
        """
        self.session = session
        self.symbol = symbol
        self.testnet = testnet
    
    def get_klines(self, interval: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """
        Get kline/candlestick data.
        
        Args:
            interval: Kline interval (e.g., '1', '5', '15', '60', 'D')
            limit: Number of candles to return (max 200)
            
        Returns:
            DataFrame with OHLCV data or None if request fails
        """
        try:
            response = self.session.get_kline(
                category="linear",
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
            
            if response['retCode'] == 0 and 'result' in response and 'list' in response['result']:
                df = pd.DataFrame(
                    response['result']['list'],
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
                )
                # Convert types
                for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
                    df[col] = pd.to_numeric(df[col])
                df['timestamp'] = pd.to_datetime(df['timestamp'].astype('int64'), unit='ms')
                return df
            return None
            
        except Exception as e:
            print(f"Error getting klines: {e}")
            return None
    
    def get_all_timeframes(self) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get kline data for multiple timeframes.
        
        Returns:
            Dictionary with interval as key and DataFrame as value
        """
        timeframes = {
            '5m': '5',
            '15m': '15',
            '1h': '60',
            '4h': '240',
            '1d': 'D'
        }
        
        return {
            tf: self.get_klines(interval=interval, limit=200)
            for tf, interval in timeframes.items()
        }
