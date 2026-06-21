import ccxt, pandas as pd, logging
from config import BITGET_API_KEY, BITGET_SECRET, BITGET_PASSPHRASE, USE_TESTNET

logger = logging.getLogger("G20Ultra")

class BitgetExchange:
    def __init__(self):
        self.exchange = ccxt.bitget({
            'apiKey':BITGET_API_KEY,'secret':BITGET_SECRET,
            'password':BITGET_PASSPHRASE,'enableRateLimit':True,
            'options':{'defaultType':'spot'}
        })
        if USE_TESTNET: self.exchange.set_sandbox_mode(True)

    def get_ohlcv(self, symbol, timeframe='4h', limit=300):
        try:
            d = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(d, columns=['timestamp','open','high','low','close','volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"OHLCV {symbol}: {e}"); return pd.DataFrame()

    def get_balance(self, asset='USDT'):
        try:
            b = self.exchange.fetch_balance()
            return float(b['free'].get(asset, 0))
        except Exception as e:
            logger.error(f"Balance: {e}"); return 0.0

    def get_all_balances(self):
        try:
            b = self.exchange.fetch_balance()
            return {k:v for k,v in b['free'].items() if float(v)>0}
        except: return {}

    def get_price(self, symbol):
        try: return float(self.exchange.fetch_ticker(symbol)['last'])
        except: return 0.0

    def market_buy(self, symbol, amount):
        try:
            o = self.exchange.create_market_buy_order(symbol, amount)
            logger.info(f"BUY {symbol} x{amount}"); return o
        except Exception as e:
            logger.error(f"Buy error: {e}"); return {}

    def market_sell(self, symbol, amount):
        try:
            o = self.exchange.create_market_sell_order(symbol, amount)
            logger.info(f"SELL {symbol} x{amount}"); return o
        except Exception as e:
            logger.error(f"Sell error: {e}"); return {}

    def ping(self):
        try: self.exchange.load_markets(); return True
        except Exception as e:
            logger.error(f"Ping fail: {e}"); return False
