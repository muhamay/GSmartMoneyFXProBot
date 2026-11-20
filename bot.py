import os, time, requests, threading
from datetime import datetime
from zoneinfo import ZoneInfo

TG_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
DATA_KEY=os.getenv("TWELVE_DATA_API_KEY","").strip()
if not TG_TOKEN or not DATA_KEY:
    raise SystemExit("Set TELEGRAM_BOT_TOKEN and TWELVE_DATA_API_KEY environment variables.")
TG="https://api.telegram.org/bot"+TG_TOKEN
DATA="https://api.twelvedata.com/time_series"
PAIRS={"XAUUSD":"XAU/USD","EURUSD":"EUR/USD","GBPUSD":"GBP/USD","USDJPY":"USD/JPY","BTCUSD":"BTC/USD","AUDUSD":"AUD/USD","GBPJPY":"GBP/JPY"}
TF={"M5":"5min","M15":"15min","M30":"30min","H1":"1h","H4":"4h","D1":"1day"}
users=set(); monitors=set(); last_alert={}; offset=0

def send(chat,msg):
    try: requests.post(TG+"/sendMessage",json={"chat_id":chat,"text":msg,"parse_mode":"HTML"},timeout=15)
    except Exception as e: print("send error",e)

def candles(pair,tf):
    r=requests.get(DATA,params={"symbol":pair,"interval":tf,"apikey":DATA_KEY,"outputsize":80},timeout=20)
    j=r.json()
    if "values" not in j: raise ValueError(j.get("message","Data provider error"))
    return j["values"]

def analysis(symbol,tf):
    pair=PAIRS.get(symbol)
    if not pair: return "Pair tidak dikenal."
    rows=candles(pair,TF.get(tf,"15min"))
    rows=list(reversed(rows))
    closes=[float(x["close"]) for x in rows]
    highs=[float(x["high"]) for x in rows]
    lows=[float(x["low"]) for x in rows]
    price=closes[-1]
    ma_fast=sum(closes[-10:])/10; ma_slow=sum(closes[-30:])/30
    trend="Bullish" if ma_fast>ma_slow else "Bearish" if ma_fast<ma_slow else "Sideways"
    # Simple heuristic candidate conditions, not a validated SMC strategy
    sweep_low=lows[-1]<min(lows[-6:-1]) and closes[-1]>lows[-1]
    sweep_high=highs[-1]>max(highs[-6:-1]) and closes[-1]<highs[-1]
    status="WAIT / NO SETUP"
    rationale="Belum ada kondisi yang cukup untuk kandidat setup."
    zone="—"; sl="—"; tp1="—"; tp2="—"; tp3="—"
    if sweep_low and trend=="Bullish":
        status="SETUP DEVELOPING — WAIT"
        rationale="Kandidat sweep low + bias trend bullish; tunggu konfirmasi tambahan."
        zone=f"{price:.5f}"
    elif sweep_high and trend=="Bearish":
        status="SETUP DEVELOPING — WAIT"
        rationale="Kandidat sweep high + bias trend bearish; tunggu konfirmasi tambahan."
        zone=f"{price:.5f}"
    score=sum([trend!="Sideways",sweep_low or sweep_high,ma_fast!=ma_slow])
    return f"""<b>G.SMART MONEY FX ✨</b>
<b>{symbol} | {tf}</b>

Status: <b>{status}</b>
Trend heuristic: {trend}
Confluence score: {score}/3
Price: <code>{price}</code>
Reference zone: <code>{zone}</code>
SL reference: {sl}
TP1: {tp1} | TP2: {tp2} | TP3: {tp3}

{rationale}

<i>Heuristic screening only; not a verified signal or financial advice. Confirm prices and risk independently.</i>"""

def menu(chat):
    send(chat,"<b>G.SMART MONEY FX ✨</b>\n\n/analyze XAUUSD [M15]\n/market\n/pairs\n/monitor\n/stopmonitor\n/help\n\nBot analisis; bukan auto-trading.")

def handle(chat,text):
    parts=text.strip().split()
    cmd=parts[0].split("@")[0].lower()
    if cmd in ("/start","/help"): menu(chat)
    elif cmd=="/pairs": send(chat,"Pairs: "+", ".join(PAIRS.keys())+"\nTimeframe: "+", ".join(TF.keys()))
    elif cmd=="/analyze":
        sym=parts[1].upper() if len(parts)>1 else "XAUUSD"
        tf=parts[2].upper() if len(parts)>2 else "M15"
        if tf not in TF: tf="M15"
        try: send(chat,analysis(sym,tf))
        except Exception as e: send(chat,"Data/analisis gagal: "+str(e))
    elif cmd=="/market":
        out=[]
        for s in PAIRS:
            try:
                rows=candles(PAIRS[s],"15min"); price=float(rows[0]["close"])
                out.append(f"{s}: <code>{price}</code>")
            except Exception as e: out.append(f"{s}: data unavailable")
        send(chat,"<b>Market snapshot (M15)</b>\n"+"\n".join(out))
    elif cmd=="/monitor":
        monitors.add(chat); send(chat,"Pemantauan otomatis aktif. Bot akan memeriksa kandidat setup setiap 5 menit.")
    elif cmd=="/stopmonitor":
        monitors.discard(chat); send(chat,"Pemantauan otomatis dimatikan.")
    else: send(chat,"Perintah tidak dikenal. Ketik /help.")

def poll():
    global offset
    while True:
        try:
            r=requests.get(TG+"/getUpdates",params={"offset":offset,"timeout":25},timeout=30).json()
            for u in r.get("result",[]):
                offset=u["update_id"]+1
                m=u.get("message",{})
                if m.get("text"): handle(m["chat"]["id"],m["text"])
        except Exception as e: print("poll",e); time.sleep(3)

def monitor():
    while True:
        for chat in list(monitors):
            for s in PAIRS:
                try:
                    msg=analysis(s,"M15")
                    if "SETUP DEVELOPING" in msg:
                        key=str(chat)+s
                        now=time.time()
                        if now-last_alert.get(key,0)>1800:
                            send(chat,msg); last_alert[key]=now
                except Exception as e: print("monitor",e)
        time.sleep(300)

if __name__=="__main__":
    print("G.SMART MONEY FX Telegram bot started.")
    threading.Thread(target=monitor,daemon=True).start()
    poll()
