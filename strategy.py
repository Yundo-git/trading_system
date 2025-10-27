# strategy.py - Phase 1.3 전략 로직 (백테스팅과 동일)

import pandas as pd
import numpy as np

class TradingStrategy:
    """Phase 1.3 변동성 적응형 전략 (백테스팅 동일 버전)"""
    
    def __init__(self):
        self.base_leverage = 2.0
        self.min_quality_score = 60  # 60점으로 복구
        
    def ema(self, series, period):
        """EMA 계산"""
        return series.ewm(span=period, adjust=False).mean()
    
    def rsi(self, series, period=14):
        """RSI 계산"""
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - 100 / (1 + rs)
    
    def calculate_atr(self, df, period=14):
        """ATR 계산"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        atr_pct = atr / df['close']
        return atr_pct
    
    def calculate_indicators(self, df):
        """모든 지표 계산"""
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        df['ema20'] = self.ema(df['close'], 20)
        df['ema50'] = self.ema(df['close'], 50)
        df['ema200'] = self.ema(df['close'], 200)
        df['rsi14'] = self.rsi(df['close'], 14)
        df['atr_pct'] = self.calculate_atr(df, 14)
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        return df
    
    def detect_volatility_regime(self, df, lookback=30):
        """변동성 Regime 감지"""
        if len(df) < lookback:
            return "NORMAL", 1.0
        
        current_atr = df['atr_pct'].iloc[-1]
        recent_atr_avg = df['atr_pct'].iloc[-lookback:].mean()
        
        if recent_atr_avg == 0:
            return "NORMAL", 1.0
        
        atr_ratio = current_atr / recent_atr_avg
        
        if atr_ratio < 0.7:
            return "ULTRA_LOW", atr_ratio
        elif atr_ratio < 0.9:
            return "LOW", atr_ratio
        elif atr_ratio < 1.1:
            return "NORMAL", atr_ratio
        elif atr_ratio < 1.3:
            return "HIGH", atr_ratio
        else:
            return "ULTRA_HIGH", atr_ratio
    
    def calculate_adaptive_multipliers(self, vol_regime):
        """변동성별 배율"""
        multipliers = {
            "ULTRA_LOW": {"tp1": 6.0, "tp2": 9.0, "sl": 2.0},
            "LOW": {"tp1": 5.0, "tp2": 7.5, "sl": 2.3},
            "NORMAL": {"tp1": 4.0, "tp2": 6.5, "sl": 2.5},
            "HIGH": {"tp1": 3.0, "tp2": 5.0, "sl": 3.0},
            "ULTRA_HIGH": {"tp1": 2.5, "tp2": 4.0, "sl": 3.5}
        }
        return multipliers.get(vol_regime, multipliers["NORMAL"])
    
    def calculate_targets(self, df, vol_regime):
        """익절/손절 타겟 계산"""
        atr_pct = df['atr_pct'].iloc[-1]
        mults = self.calculate_adaptive_multipliers(vol_regime)
        
        tp1_pct = atr_pct * mults["tp1"]
        tp2_pct = atr_pct * mults["tp2"]
        sl_pct = atr_pct * mults["sl"]
        
        # 안전 범위
        if vol_regime == "ULTRA_LOW":
            tp1_range, tp2_range, sl_range = (0.08, 0.20), (0.15, 0.35), (0.02, 0.06)
        elif vol_regime == "LOW":
            tp1_range, tp2_range, sl_range = (0.06, 0.18), (0.12, 0.30), (0.025, 0.07)
        elif vol_regime == "NORMAL":
            tp1_range, tp2_range, sl_range = (0.04, 0.15), (0.08, 0.25), (0.025, 0.08)
        elif vol_regime == "HIGH":
            tp1_range, tp2_range, sl_range = (0.03, 0.12), (0.06, 0.20), (0.03, 0.09)
        else:  # ULTRA_HIGH
            tp1_range, tp2_range, sl_range = (0.02, 0.10), (0.04, 0.15), (0.035, 0.10)
        
        tp1_pct = np.clip(tp1_pct, *tp1_range)
        tp2_pct = np.clip(tp2_pct, *tp2_range)
        sl_pct = min(np.clip(sl_pct, *sl_range), 0.03)  # 최대 3%
        
        return tp1_pct, tp2_pct, sl_pct
    
    def detect_market_regime(self, df):
        """시장 Regime 감지"""
        if len(df) < 50:
            return "UNKNOWN"
        
        recent = df.iloc[-50:]
        ema20_slope = (df['ema20'].iloc[-1] - df['ema20'].iloc[-21]) / 20 / df['close'].iloc[-1]
        price_above_ema = (recent.iloc[-20:]['close'] > recent.iloc[-20:]['ema20']).mean()
        returns_std = recent['returns'].std()
        
        high = recent['high'].max()
        low = recent['low'].min()
        range_pct = (high - low) / low
        
        if ema20_slope > 0.001 and price_above_ema > 0.7:
            return "TREND_UP" if returns_std < 0.03 else "VOLATILE_UP"
        elif ema20_slope < -0.001 and price_above_ema < 0.3:
            return "TREND_DOWN"
        elif range_pct < 0.15:
            return "SIDEWAYS"
        else:
            return "VOLATILE"
    
    def calculate_signal_quality(self, df_1h, df_15m):
        """시그널 품질 점수"""
        score = 0
        
        # 추세 점수
        ema20 = df_1h['ema20'].iloc[-1]
        ema50 = df_1h['ema50'].iloc[-1]
        ema200 = df_1h['ema200'].iloc[-1]
        
        if ema20 > ema50 > ema200:
            gap1 = (ema20 - ema50) / ema50
            gap2 = (ema50 - ema200) / ema200
            trend_score = min(25, (gap1 + gap2) * 1000)
            score += trend_score
        
        # 모멘텀 점수
        if len(df_1h) >= 5:
            recent_returns = df_1h['returns'].iloc[-5:]
            positive_ratio = (recent_returns > 0).mean()
            score += positive_ratio * 25
        
        # RSI 점수
        rsi = df_1h['rsi14'].iloc[-1]
        if 30 <= rsi <= 70:
            score += 25
        elif 40 <= rsi <= 60:
            score += 15
        
        # 거래량 점수
        vol_ratio = df_1h['volume'].iloc[-1] / df_1h['vol_ma20'].iloc[-1]
        if vol_ratio > 1.2:
            score += 25
        elif vol_ratio > 1.0:
            score += 15
        
        return min(100, score)
    
    def check_entry_signal(self, df_1h, df_15m, df_5m):
        """진입 시그널 확인"""
        if len(df_1h) < 200:
            return None
        
        # 기본 조건: EMA 정배열
        if not (df_1h['ema20'].iloc[-1] > df_1h['ema50'].iloc[-1] > df_1h['ema200'].iloc[-1]):
            return None
        
        # 변동성 regime
        vol_regime, atr_ratio = self.detect_volatility_regime(df_1h)
        
        # 시장 regime
        market_regime = self.detect_market_regime(df_1h)
        
        # ATR 스파이크 필터링 (백테스팅과 동일)
        atr_pct = df_1h['atr_pct'].iloc[-1]
        atr_avg = df_1h['atr_pct'].iloc[-30:].mean()
        
        if atr_pct > atr_avg * 1.5:
            # ATR 급등 시 품질 요구 상승
            min_quality = 75
        elif vol_regime == "ULTRA_HIGH":
            min_quality = 75
        else:
            min_quality = self.min_quality_score
        
        # 품질 점수
        quality = self.calculate_signal_quality(df_1h, df_15m)
        
        if quality < min_quality:
            return None
        
        # 타겟 계산
        tp1_pct, tp2_pct, sl_pct = self.calculate_targets(df_1h, vol_regime)
        
        entry_price = df_1h['close'].iloc[-1]
        
        signal = {
            'action': 'BUY',
            'entry_price': entry_price,
            'tp1_price': entry_price * (1 + tp1_pct),
            'tp2_price': entry_price * (1 + tp2_pct),
            'sl_price': entry_price * (1 - sl_pct),
            'tp1_pct': tp1_pct * 100,
            'tp2_pct': tp2_pct * 100,
            'sl_pct': sl_pct * 100,
            'quality': quality,
            'vol_regime': vol_regime,
            'atr_ratio': atr_ratio,
            'market_regime': market_regime,
            'timestamp': df_1h['timestamp'].iloc[-1]
        }
        
        return signal
    
    def calculate_trailing_stop(self, entry_price, current_price, vol_regime):
        """트레일링 스톱 계산 (백테스팅과 동일)"""
        profit_pct = (current_price - entry_price) / entry_price
        
        # 5% 이상 수익 시 트레일링 시작
        if profit_pct < 0.05:
            return None
        
        # 변동성별 트레일링 간격
        if vol_regime in ["LOW", "ULTRA_LOW"]:
            trailing_pct = 0.02  # 2%
        elif vol_regime == "NORMAL":
            trailing_pct = 0.03  # 3%
        else:  # HIGH, ULTRA_HIGH
            trailing_pct = 0.05  # 5%
        
        trailing_price = current_price * (1 - trailing_pct)
        
        return trailing_price