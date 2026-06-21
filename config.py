import os
from dataclasses import dataclass

BITGET_API_KEY    = os.getenv("BITGET_API_KEY",    "")
BITGET_SECRET     = os.getenv("BITGET_SECRET",     "")
BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID",  "")

TRADING_PAIRS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"]
TIMEFRAMES    = {"primary":"4h","confirm":"1h","higher":"1d"}
CANDLES_LIMIT = 300
LOOP_INTERVAL = 240
USE_TESTNET   = False

@dataclass
class RiskConfig:
    max_risk_per_trade: float = 0.02
    max_open_trades:    int   = 3
    max_daily_loss:     float = 0.06
    stop_loss_pct:      float = 0.025
    take_profit_pct:    float = 0.055
    trailing_stop:      bool  = True
    trailing_pct:       float = 0.015
    use_atr_stop:       bool  = True
    atr_multiplier:     float = 1.8
    min_rr_ratio:       float = 1.5

@dataclass
class StrategyParams:
    rsi_period:       int   = 14
    rsi_oversold:     float = 35.0
    rsi_overbought:   float = 65.0
    macd_fast:        int   = 12
    macd_slow:        int   = 26
    macd_signal:      int   = 9
    bb_period:        int   = 20
    bb_std:           float = 2.0
    ema_fast:         int   = 9
    ema_slow:         int   = 21
    ema_trend:        int   = 50
    stoch_period:     int   = 14
    stoch_smooth:     int   = 3
    adx_period:       int   = 14
    adx_min:          float = 20.0
    atr_period:       int   = 14
    willr_period:     int   = 14
    cci_period:       int   = 20
    volume_ma_period: int   = 20
    st_period:        int   = 7
    st_multiplier:    float = 3.0

RISK   = RiskConfig()
PARAMS = StrategyParams()

STRATEGY_WEIGHTS = {
    "rsi":1.5,"macd":2.0,"bollinger":1.5,"ema_cross":2.0,
    "supertrend":2.0,"stoch_rsi":1.5,"adx_filter":1.0,
    "volume_surge":1.0,"vwap":1.5,"cci":1.0,"williams_r":1.0,
    "trend_filter":2.0,"divergence":2.0,"order_flow":1.5,"heikin_ashi":1.0,
}

BUY_SCORE_THRESHOLD  = 8.0
SELL_SCORE_THRESHOLD = 8.0
LOG_FILE  = "logs/g20_ultra.log"
TRADES_DB = "data/trades.json"
REPORT_HOUR = [0,4,8,12,16,20]
