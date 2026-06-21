import sys, time, logging, traceback, os
from datetime import datetime

sys.path.insert(0,'.')
sys.path.insert(0,'./strategies')
sys.path.insert(0,'./core')
sys.path.insert(0,'./utils')

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

from config import TRADING_PAIRS, TIMEFRAMES, CANDLES_LIMIT, LOOP_INTERVAL, REPORT_HOUR, LOG_FILE
from strategies.engine import calculate_score
from core.exchange     import BitgetExchange
from core.risk_manager import RiskManager
from utils.notifier    import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.FileHandler(LOG_FILE,encoding='utf-8'),logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("G20Ultra")

class G20UltraBot:
    def __init__(self):
        logger.info("🚀 تهيئة G20 Ultra Bot...")
        self.exchange = BitgetExchange()
        self.risk     = RiskManager()
        self.notify   = TelegramNotifier()
        self.last_rpt = -1
        if not self.exchange.ping():
            logger.error("❌ فشل الاتصال بـ Bitget"); sys.exit(1)
        bal = self.exchange.get_balance('USDT')
        logger.info(f"✅ اتصال ناجح | USDT: {bal:.2f}")
        self.notify.send(f"🟢 <b>G20 Ultra Bot بدأ ✅</b>\n💰 USDT: <code>{bal:.2f}</code>\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    def run(self):
        logger.info(f"⚙️ البوت يعمل على {len(TRADING_PAIRS)} زوج")
        while True:
            try:
                self._cycle()
                self._maybe_report()
                logger.info(f"💤 انتظار {LOOP_INTERVAL}ث...")
                time.sleep(LOOP_INTERVAL)
            except KeyboardInterrupt:
                logger.info("⛔ إيقاف")
                self.notify.send("⛔ <b>G20 Ultra Bot أُوقف</b>"); break
            except Exception as e:
                logger.error(f"❌ خطأ: {e}")
                self.notify.error_alert(traceback.format_exc()[:400],"Main Loop")
                time.sleep(60)

    def _cycle(self):
        logger.info(f"🔄 دورة {datetime.now().strftime('%H:%M:%S')}")
        capital = self.exchange.get_balance('USDT')
        if capital<5:
            logger.warning("⚠️ رصيد منخفض"); return
        for symbol in TRADING_PAIRS:
            try: self._analyze(symbol, capital)
            except Exception as e: logger.error(f"خطأ {symbol}: {e}")

    def _analyze(self, symbol, capital):
        df       = self.exchange.get_ohlcv(symbol, TIMEFRAMES['primary'], CANDLES_LIMIT)
        df_daily = self.exchange.get_ohlcv(symbol, TIMEFRAMES['higher'],  250)
        if df.empty or len(df)<100: return
        price = float(df['close'].iloc[-1])
        exit_r = self.risk.check_exits(symbol, price)
        if exit_r and symbol in self.risk.open_trades:
            t = self.risk.open_trades[symbol]
            if self.exchange.market_sell(symbol, t['amount']):
                res = self.risk.close_trade(symbol, price, exit_r)
                self.notify.trade_closed(res)
            return
        if symbol in self.risk.open_trades: return
        ok, reason = self.risk.can_trade()
        if not ok: logger.info(f"⛔ {reason}"); return
        result = calculate_score(df, df_daily if not df_daily.empty else None)
        dec, bs = result['decision'], result['buy_score']
        logger.info(f"📊 {symbol} BUY={bs:.1f} SELL={result['sell_score']:.1f} → {dec}")
        if dec=="BUY":
            amt, sl, tp = self.risk.position_size(capital, price, df)
            if self.exchange.market_buy(symbol, amt):
                self.risk.open_trade(symbol,'buy',price,amt,sl,tp)
                self.notify.trade_signal(symbol,"BUY",price,amt,sl,tp,bs,result['signals'])
                logger.info(f"✅ شراء {symbol} x{amt} @ {price:.4f}")

    def _maybe_report(self):
        h = datetime.now().hour
        if h in REPORT_HOUR and h!=self.last_rpt:
            self.last_rpt = h
            self.notify.periodic_report(
                self.exchange.get_all_balances(),
                self.risk.performance_stats(),
                self.risk.open_trades,
                {s:self.exchange.get_price(s) for s in self.risk.open_trades}
            )

if __name__=="__main__":
    G20UltraBot().run()
