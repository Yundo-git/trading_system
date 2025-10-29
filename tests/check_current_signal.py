# check_current_signal.py - 현재 시그널 상태 상세 확인

from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os
from data_collector import DataCollector
from strategy import TradingStrategy

load_dotenv()

session = HTTP(
    testnet=True,
    api_key=os.getenv('BYBIT_TESTNET_API_KEY'),
    api_secret=os.getenv('BYBIT_TESTNET_API_SECRET'),
    recv_window=60000
)

symbol = 'BTCUSDT'
collector = DataCollector(session, symbol, True)
strategy = TradingStrategy()

print("=" * 80)
print(f"📊 {symbol} 현재 시장 상태")
print("=" * 80)

# 데이터 수집
data = collector.get_all_timeframes()
df_1h = strategy.calculate_indicators(data['1h'])

# 현재 상태
current_price = df_1h['close'].iloc[-1]
ema20 = df_1h['ema20'].iloc[-1]
ema50 = df_1h['ema50'].iloc[-1]
ema200 = df_1h['ema200'].iloc[-1]
rsi = df_1h['rsi14'].iloc[-1]
atr_pct = df_1h['atr_pct'].iloc[-1]

print(f"\n💰 현재가: ${current_price:,.2f}")
print(f"\n📈 EMA 상태:")
print(f"   EMA20:  ${ema20:,.2f}")
print(f"   EMA50:  ${ema50:,.2f}")
print(f"   EMA200: ${ema200:,.2f}")

if ema20 > ema50 > ema200:
    print(f"   ✅ 정배열 (상승 추세)")
else:
    print(f"   ❌ 정배열 아님")

print(f"\n📊 지표:")
print(f"   RSI: {rsi:.2f}")
print(f"   ATR: {atr_pct*100:.2f}%")

# 변동성 regime
vol_regime, atr_ratio = strategy.detect_volatility_regime(df_1h)
print(f"\n🌡️  변동성: {vol_regime} (비율: {atr_ratio:.2f})")

# 시장 regime
market_regime = strategy.detect_market_regime(df_1h)
print(f"📈 시장 상태: {market_regime}")

# 품질 점수
quality = strategy.calculate_signal_quality(df_1h, strategy.calculate_indicators(data['15m']))
print(f"\n⭐ 품질 점수: {quality:.0f}점 (최소: 60점)")

print("\n" + "=" * 80)