import pandas_ta as ta, json, os
from datetime import datetime, date
from config import RISK, PARAMS, TRADES_DB

class RiskManager:
    def __init__(self):
        self.open_trades = {}
        self.daily_pnl   = 0.0
        self.daily_date  = date.today()
        self.all_trades  = self._load()

    def position_size(self, capital, entry, df):
        atr = self._atr(df)
        sl_dist = atr*RISK.atr_multiplier if (RISK.use_atr_stop and atr>0) else entry*RISK.stop_loss_pct
        tp_dist = sl_dist * max(RISK.min_rr_ratio, 2.2)
        pos = min((capital*RISK.max_risk_per_trade)/sl_dist, (capital*0.25)/entry)
        return round(pos,6), round(entry-sl_dist,6), round(entry+tp_dist,6)

    def can_trade(self):
        if date.today()!=self.daily_date:
            self.daily_pnl=0.0; self.daily_date=date.today()
        if len(self.open_trades)>=RISK.max_open_trades:
            return False, f"حد الصفقات ({RISK.max_open_trades})"
        if self.daily_pnl<=-(RISK.max_daily_loss):
            return False, "حد الخسارة اليومي"
        return True, "OK"

    def open_trade(self, symbol, side, entry, amount, sl, tp):
        self.open_trades[symbol] = {
            "symbol":symbol,"side":side,"entry_price":entry,
            "amount":amount,"stop_loss":sl,"take_profit":tp,
            "open_time":datetime.now().isoformat(),"max_price":entry
        }

    def close_trade(self, symbol, exit_price, reason):
        if symbol not in self.open_trades: return {}
        t = self.open_trades.pop(symbol)
        fee = 0.001
        gross = (exit_price-t['entry_price'])*t['amount']
        fees  = (t['entry_price']+exit_price)*t['amount']*fee
        net   = gross-fees
        pct   = net/(t['entry_price']*t['amount'])*100
        r = {**t,"exit_price":exit_price,"close_time":datetime.now().isoformat(),
             "reason":reason,"net_pnl":round(net,4),"pnl_pct":round(pct,2),"fees":round(fees,4)}
        self.all_trades.append(r); self.daily_pnl+=net; self._save(); return r

    def check_exits(self, symbol, price):
        if symbol not in self.open_trades: return None
        t = self.open_trades[symbol]
        if price>t.get('max_price',0): self.open_trades[symbol]['max_price']=price
        if RISK.trailing_stop:
            new_sl = price - t['entry_price']*RISK.trailing_pct
            if new_sl>t['stop_loss']: self.open_trades[symbol]['stop_loss']=new_sl
        if price<=self.open_trades[symbol]['stop_loss']: return 'SL'
        if price>=t['take_profit']: return 'TP'
        return None

    def performance_stats(self):
        if not self.all_trades: return {"message":"لا توجد صفقات بعد"}
        pnls = [t['net_pnl'] for t in self.all_trades]
        wins = [p for p in pnls if p>0]
        loss = [p for p in pnls if p<0]
        wr   = len(wins)/len(pnls)*100
        pf   = abs(sum(wins)/sum(loss)) if loss else 999
        cum=[]; r=0
        for p in pnls: r+=p; cum.append(r)
        pk = max(cum) if cum else 0
        dd = max([(pk-c)/abs(pk)*100 for c in cum if pk!=0], default=0)
        return {"total_trades":len(pnls),"win_rate":round(wr,1),
                "total_pnl":round(sum(pnls),4),"profit_factor":round(pf,2),
                "max_drawdown":round(dd,1),"daily_pnl":round(self.daily_pnl,4)}

    def _atr(self, df):
        a = ta.atr(df['high'],df['low'],df['close'],length=PARAMS.atr_period)
        return float(a.iloc[-1]) if a is not None else 0.0

    def _load(self):
        if os.path.exists(TRADES_DB):
            with open(TRADES_DB) as f: return json.load(f)
        return []

    def _save(self):
        os.makedirs(os.path.dirname(TRADES_DB), exist_ok=True)
        with open(TRADES_DB,'w') as f: json.dump(self.all_trades,f,indent=2,ensure_ascii=False)
