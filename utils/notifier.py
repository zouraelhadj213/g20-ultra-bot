import asyncio, logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("G20Ultra")

class TelegramNotifier:
    def __init__(self):
        self.bot     = Bot(token=TELEGRAM_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID

    def _run(self, coro):
        try: asyncio.run(coro)
        except Exception as e: logger.error(f"Telegram: {e}")

    async def _send(self, text):
        try: await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='HTML')
        except TelegramError as e: logger.error(f"TG error: {e}")

    def send(self, text): self._run(self._send(text))

    def trade_signal(self, symbol, action, price, amount, sl, tp, score, signals):
        e = "🟢" if action=="BUY" else "🔴"
        rr = round((tp-price)/(price-sl),2) if price!=sl else 0
        top = [v['label'] for k,v in signals.items() if v['signal']>0][:5]
        sigs = "\n".join(f"  ✅ {s}" for s in top) or "  —"
        self.send(f"{e} <b>إشارة {action}</b>\n━━━━━━━━━━━━━━\n📌 {symbol}\n💰 ${price:,.4f}\n📦 {amount}\n🛑 SL: ${sl:,.4f}\n🎯 TP: ${tp:,.4f}\n⚖️ R:R {rr}\n🏆 {score:.1f} نقطة\n\n<b>إشارات:</b>\n{sigs}\n⏰ {datetime.now().strftime('%H:%M:%S')}")

    def trade_closed(self, r):
        e  = "💚" if r.get('net_pnl',0)>0 else "💔"
        re = "🎯" if r.get('reason')=="TP" else "🛑"
        self.send(f"{e} <b>صفقة مُغلقة</b>\n━━━━━━━━━━━━━━\n📌 {r.get('symbol')}\n{re} {r.get('reason')}\n📥 ${r.get('entry_price',0):,.4f}\n📤 ${r.get('exit_price',0):,.4f}\n{'📈' if r.get('net_pnl',0)>0 else '📉'} PnL: <b>${r.get('net_pnl',0):+.4f} ({r.get('pnl_pct',0):+.2f}%)</b>")

    def periodic_report(self, balances, stats, open_trades, prices):
        bal = "\n".join(f"  {k}: {v:.4f}" for k,v in balances.items()) or "  —"
        ops = ""
        for sym,t in open_trades.items():
            cur = prices.get(sym, t['entry_price'])
            upl = (cur-t['entry_price'])*t['amount']
            ops += f"\n  📍 {sym}: ${cur:.4f} | {upl:+.4f}"
        if not ops: ops = "\n  — لا صفقات مفتوحة"
        self.send(f"📊 <b>تقرير G20 Ultra</b>\n━━━━━━━━━━━━━━\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n💼 الأرصدة:\n{bal}\n\n📈 الصفقات:{ops}\n\n🏆 الأداء:\n  صفقات: {stats.get('total_trades',0)}\n  Win Rate: {stats.get('win_rate',0):.1f}%\n  PF: {stats.get('profit_factor',0):.2f}\n  PnL: ${stats.get('total_pnl',0):+.4f}\n  DD: {stats.get('max_drawdown',0):.1f}%")

    def error_alert(self, err, ctx=""):
        self.send(f"⚠️ <b>خطأ</b>\n{ctx}\n{err[:300]}")
