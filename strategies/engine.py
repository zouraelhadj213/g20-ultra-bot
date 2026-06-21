import pandas as pd
import pandas_ta as ta
from config import PARAMS, STRATEGY_WEIGHTS, BUY_SCORE_THRESHOLD, SELL_SCORE_THRESHOLD

def to_heikin_ashi(df):
    ha = df.copy()
    ha['ha_close'] = (df['open']+df['high']+df['low']+df['close'])/4
    ha['ha_open'] = 0.0
    ha.loc[ha.index[0],'ha_open'] = (df['open'].iloc[0]+df['close'].iloc[0])/2
    for i in range(1,len(ha)):
        ha.iloc[i, ha.columns.get_loc('ha_open')] = (ha['ha_open'].iloc[i-1]+ha['ha_close'].iloc[i-1])/2
    ha['ha_high'] = ha[['high','ha_open','ha_close']].max(axis=1)
    ha['ha_low']  = ha[['low','ha_open','ha_close']].min(axis=1)
    return ha

def rsi_signal(df):
    rsi = ta.rsi(df['close'], length=PARAMS.rsi_period)
    l,p = rsi.iloc[-1], rsi.iloc[-2]
    if l<PARAMS.rsi_oversold and l>p: return 1, f"RSI شراء ({l:.1f})"
    if l>PARAMS.rsi_overbought and l<p: return -1, f"RSI بيع ({l:.1f})"
    return 0, f"RSI محايد ({l:.1f})"

def macd_signal(df):
    m = ta.macd(df['close'], fast=PARAMS.macd_fast, slow=PARAMS.macd_slow, signal=PARAMS.macd_signal)
    macd,sig,hist = m.iloc[:,0],m.iloc[:,2],m.iloc[:,1]
    if (macd.iloc[-1]>sig.iloc[-1]) and (macd.iloc[-2]<=sig.iloc[-2]) and hist.iloc[-1]>hist.iloc[-2]:
        return 1,"MACD تقاطع صاعد"
    if (macd.iloc[-1]<sig.iloc[-1]) and (macd.iloc[-2]>=sig.iloc[-2]):
        return -1,"MACD تقاطع هابط"
    return 0,"MACD محايد"

def bollinger_signal(df):
    bb = ta.bbands(df['close'], length=PARAMS.bb_period, std=PARAMS.bb_std)
    upper,lower = bb.iloc[:,0],bb.iloc[:,2]
    c = df['close']
    if c.iloc[-2]<=lower.iloc[-2] and c.iloc[-1]>lower.iloc[-1]: return 1,"BB ارتداد أسفل"
    if c.iloc[-2]>=upper.iloc[-2] and c.iloc[-1]<upper.iloc[-1]: return -1,"BB ارتداد أعلى"
    return 0,"BB محايد"

def ema_cross_signal(df):
    e9  = ta.ema(df['close'], length=PARAMS.ema_fast)
    e21 = ta.ema(df['close'], length=PARAMS.ema_slow)
    e50 = ta.ema(df['close'], length=PARAMS.ema_trend)
    bull = e9.iloc[-1]>e21.iloc[-1]>e50.iloc[-1]
    bear = e9.iloc[-1]<e21.iloc[-1]<e50.iloc[-1]
    cup = (e9.iloc[-1]>e21.iloc[-1]) and (e9.iloc[-2]<=e21.iloc[-2])
    cdn = (e9.iloc[-1]<e21.iloc[-1]) and (e9.iloc[-2]>=e21.iloc[-2])
    if bull and cup: return 1,"EMA تقاطع صاعد"
    if bear and cdn: return -1,"EMA تقاطع هابط"
    if bull: return 0.5,"EMA اتجاه صاعد"
    if bear: return -0.5,"EMA اتجاه هابط"
    return 0,"EMA محايد"

def supertrend_signal(df):
    try:
        st = ta.supertrend(df['high'],df['low'],df['close'],
                           length=PARAMS.st_period,multiplier=PARAMS.st_multiplier)
        col = [c for c in st.columns if c.startswith('SUPERTd')][0]
        cur,prev = st[col].iloc[-1],st[col].iloc[-2]
        if cur==1 and prev==-1: return 1,"Supertrend تحول صاعد 🚀"
        if cur==-1 and prev==1: return -1,"Supertrend تحول هابط 🔻"
        if cur==1: return 0.5,"Supertrend صاعد"
        return -0.5,"Supertrend هابط"
    except: return 0,"Supertrend خطأ"

def stoch_rsi_signal(df):
    try:
        s = ta.stochrsi(df['close'],length=PARAMS.stoch_period,
                        smooth_k=PARAMS.stoch_smooth,smooth_d=PARAMS.stoch_smooth)
        k,d = s.iloc[:,0],s.iloc[:,1]
        if (k.iloc[-1]>d.iloc[-1]) and (k.iloc[-2]<=d.iloc[-2]) and k.iloc[-1]<20:
            return 1,"StochRSI تشبع بيعي"
        if (k.iloc[-1]<d.iloc[-1]) and (k.iloc[-2]>=d.iloc[-2]) and k.iloc[-1]>80:
            return -1,"StochRSI تشبع شرائي"
    except: pass
    return 0,"StochRSI محايد"

def adx_filter(df):
    try:
        a = ta.adx(df['high'],df['low'],df['close'],length=PARAMS.adx_period)
        val = a.iloc[:,0].iloc[-1]
        return val>PARAMS.adx_min, f"ADX={val:.1f}"
    except: return True,"ADX خطأ"

def volume_signal(df):
    vol = df['volume']
    ma  = vol.rolling(PARAMS.volume_ma_period).mean()
    r   = vol.iloc[-1]/ma.iloc[-1]
    up  = df['close'].iloc[-1]>df['close'].iloc[-2]
    if r>1.5 and up:  return 1, f"Volume صعود ({r:.1f}x)"
    if r>1.5 and not up: return -1, f"Volume هبوط ({r:.1f}x)"
    return 0, f"Volume طبيعي ({r:.1f}x)"

def vwap_signal(df):
    try:
        vwap = ta.vwap(df['high'],df['low'],df['close'],df['volume'])
        c,v  = df['close'].iloc[-1],vwap.iloc[-1]
        if c>v*1.001: return 1, f"VWAP فوق"
        if c<v*0.999: return -1,"VWAP تحت"
    except: pass
    return 0,"VWAP محايد"

def cci_signal(df):
    cci = ta.cci(df['high'],df['low'],df['close'],length=PARAMS.cci_period)
    v,p = cci.iloc[-1],cci.iloc[-2]
    if v>-100 and p<=-100: return 1, f"CCI تشبع بيعي ({v:.0f})"
    if v<100  and p>=100:  return -1,f"CCI تشبع شرائي ({v:.0f})"
    return 0,f"CCI محايد ({v:.0f})"

def williams_r_signal(df):
    w = ta.willr(df['high'],df['low'],df['close'],length=PARAMS.willr_period)
    v,p = w.iloc[-1],w.iloc[-2]
    if v>-80 and p<=-80: return 1, f"Williams تشبع بيعي ({v:.1f})"
    if v<-20 and p>=-20: return -1,f"Williams تشبع شرائي ({v:.1f})"
    return 0,f"Williams محايد ({v:.1f})"

def trend_filter_signal(df_daily):
    try:
        e50  = ta.ema(df_daily['close'],length=50)
        e200 = ta.ema(df_daily['close'],length=200)
        c    = df_daily['close'].iloc[-1]
        if c>e50.iloc[-1]>e200.iloc[-1]: return 1,"Trend يومي صاعد ✅"
        if c<e50.iloc[-1]<e200.iloc[-1]: return -1,"Trend يومي هابط ❌"
    except: pass
    return 0,"Trend غير محدد"

def divergence_signal(df):
    try:
        rsi = ta.rsi(df['close'],length=PARAMS.rsi_period)
        c   = df['close']
        lp  = c.iloc[-10:].nsmallest(2).index.tolist()
        hp  = c.iloc[-10:].nlargest(2).index.tolist()
        if len(lp)>=2 and c[lp[1]]<c[lp[0]] and rsi[lp[1]]>rsi[lp[0]]:
            return 1,"Divergence صعودي 🔄"
        if len(hp)>=2 and c[hp[1]]>c[hp[0]] and rsi[hp[1]]<rsi[hp[0]]:
            return -1,"Divergence هبوطي 🔄"
    except: pass
    return 0,"لا divergence"

def order_flow_signal(df):
    o,h,l,c = df['open'].iloc[-1],df['high'].iloc[-1],df['low'].iloc[-1],df['close'].iloc[-1]
    r = h-l
    if r==0: return 0,"Order Flow غير صالح"
    lw = (min(o,c)-l)/r
    uw = (h-max(o,c))/r
    bd = abs(c-o)/r
    if lw>0.6 and bd<0.35 and c>o: return 1,"Hammer 🔨"
    if uw>0.6 and bd<0.35 and c<o: return -1,"Shooting Star ⭐"
    po,pc = df['open'].iloc[-2],df['close'].iloc[-2]
    if pc<po and c>o and c>po and o<pc: return 1,"Bullish Engulfing 📈"
    if pc>po and c<o and c<po and o>pc: return -1,"Bearish Engulfing 📉"
    return 0,"لا نمط"

def heikin_ashi_signal(df):
    ha   = to_heikin_ashi(df)
    last = ha.tail(3)
    if all(last['ha_close']>last['ha_open']): return 1,"Heikin Ashi صاعد 💚"
    if all(last['ha_close']<last['ha_open']): return -1,"Heikin Ashi هابط 🔴"
    return 0,"Heikin Ashi مختلط"

def calculate_score(df, df_daily=None):
    strategies = {
        "rsi":rsi_signal,"macd":macd_signal,"bollinger":bollinger_signal,
        "ema_cross":ema_cross_signal,"supertrend":supertrend_signal,
        "stoch_rsi":stoch_rsi_signal,"volume_surge":volume_signal,
        "vwap":vwap_signal,"cci":cci_signal,"williams_r":williams_r_signal,
        "divergence":divergence_signal,"order_flow":order_flow_signal,
        "heikin_ashi":heikin_ashi_signal,
    }
    signals    = {}
    buy_score  = 0.0
    sell_score = 0.0
    for name,func in strategies.items():
        try:
            sig,label = func(df)
            w = STRATEGY_WEIGHTS.get(name,1.0)
            signals[name] = {"signal":sig,"label":label,"weight":w}
            if sig>0:   buy_score  += sig*w
            elif sig<0: sell_score += abs(sig)*w
        except Exception as e:
            signals[name] = {"signal":0,"label":f"خطأ:{e}","weight":0}
    adx_ok,adx_label = adx_filter(df)
    signals["adx_filter"] = {"signal":1 if adx_ok else 0,"label":adx_label,"weight":1.0}
    if df_daily is not None and len(df_daily)>200:
        t,tl = trend_filter_signal(df_daily)
        signals["trend_filter"] = {"signal":t,"label":tl,"weight":2.0}
        if t>0:   buy_score  += 2.0
        elif t<0: sell_score += 2.0
    else:
        signals["trend_filter"] = {"signal":0,"label":"Trend: لا بيانات","weight":0}
    decision = "HOLD"
    if buy_score>=BUY_SCORE_THRESHOLD   and adx_ok: decision = "BUY"
    elif sell_score>=SELL_SCORE_THRESHOLD and adx_ok: decision = "SELL"
    return {"decision":decision,"buy_score":round(buy_score,2),
            "sell_score":round(sell_score,2),"signals":signals,"adx_ok":adx_ok}
