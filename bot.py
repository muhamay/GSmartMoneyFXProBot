import os,time,requests,threading,datetime
from statistics import mean
from zoneinfo import ZoneInfo
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip(); KEY=os.getenv("TWELVE_DATA_API_KEY","").strip()
if not TOKEN or not KEY: raise SystemExit("Configure TELEGRAM_BOT_TOKEN and TWELVE_DATA_API_KEY.")
TG=f"https://api.telegram.org/bot{TOKEN}"; API="https://api.twelvedata.com/time_series"
SYMS={"XAUUSD":"XAU/USD","EURUSD":"EUR/USD","GBPUSD":"GBP/USD","USDJPY":"USD/JPY","BTCUSD":"BTC/USD","AUDUSD":"AUD/USD","GBPJPY":"GBP/JPY"}
TFS={"M5":"5min","M15":"15min","M30":"30min","H1":"1h","H4":"4h","D1":"1day"}
monitor=set(); last_alert={}; offset=0
def send(chat,s):
 try: requests.post(TG+"/sendMessage",json={"chat_id":chat,"text":s,"parse_mode":"HTML"},timeout=15)
 except Exception as e: print(e)
def candles(pair,tf,size=120):
 j=requests.get(API,params={"symbol":pair,"interval":tf,"apikey":KEY,"outputsize":size},timeout=20).json()
 if "values" not in j: raise RuntimeError(j.get("message","provider unavailable"))
 return list(reversed(j["values"]))
def pivot(vals,i,w=2):
 return vals[i]==max(vals[i-w:i+w+1]) or vals[i]==min(vals[i-w:i+w+1])
def session_now():
 # Session schedule approximations in UTC; DST boundaries vary. informational filter.
 utc=datetime.datetime.now(datetime.timezone.utc)
 t=utc.hour+utc.minute/60
 london=7<=t<16
 ny=12<=t<21
 return london,ny,utc
def news_gate():
 # No calendar feed integrated in this build: report unavailable, never falsely claim clean news.
 return "NEWS CALENDAR UNAVAILABLE — manual news check required"
def analyze(sym,tf):
 pair=SYMS.get(sym)
 if not pair: raise ValueError("Unknown symbol")
 data=candles(pair,TFS.get(tf,"15min"),120)
 c=[float(x["close"]) for x in data]; h=[float(x["high"]) for x in data]; l=[float(x["low"]) for x in data]; o=[float(x["open"]) for x in data]
 px=c[-1]
 # recent confirmed pivot candidates
 pivH=[h[i] for i in range(2,len(h)-2) if h[i]==max(h[i-2:i+3])]
 pivL=[l[i] for i in range(2,len(l)-2) if l[i]==min(l[i-2:i+3])]
 swingH=pivH[-1] if pivH else max(h[-20:-1]); swingL=pivL[-1] if pivL else min(l[-20:-1])
 sweepL=l[-1]<swingL and c[-1]>swingL; sweepH=h[-1]>swingH and c[-1]<swingH
 bosUp=px>swingH; bosDn=px<swingL
 # FVG recent window scan, report nearest unfilled candidate
 fvg=None; fvgdir=None
 for i in range(len(data)-1,2,-1):
  if l[i]>h[i-2]: fvg=(h[i-2],l[i]);fvgdir="Bullish";break
  if h[i]<l[i-2]: fvg=(h[i],l[i-2]);fvgdir="Bearish";break
 ob=None; obdir=None
 for i in range(len(data)-2, max(1,len(data)-25),-1):
  if bosUp and c[i]<o[i] and c[-1]>h[i]:ob=(l[i],h[i]);obdir="Bullish";break
  if bosDn and c[i]>o[i] and c[-1]<l[i]:ob=(l[i],h[i]);obdir="Bearish";break
 # HTF vote, moving average trend
 htf="1h" if tf in ("M5","M15","M30") else "4h" if tf=="H1" else "1day"
 try:
  hd=candles(pair,htf,60); hc=[float(x["close"]) for x in hd]
  htb="Bullish" if mean(hc[-10:])>mean(hc[-30:]) else "Bearish" if mean(hc[-10:])<mean(hc[-30:]) else "Neutral"
 except: htb="Unavailable"
 # session gate
 london,ny,utc=session_now()
 session="LONDON" if london else "NEW YORK" if ny else "OUTSIDE LONDON/NY"
 # Score
 struct="Bullish" if bosUp else "Bearish" if bosDn else "Neutral"
 score=0; checks=[]
 if sweepL or sweepH: score+=2;checks.append("Sweep")
 if bosUp or bosDn:score+=2;checks.append("BOS")
 if fvg:score+=1;checks.append("FVG")
 if ob:score+=1;checks.append("OB")
 if htb==struct and struct!="Neutral":score+=2;checks.append("HTF align")
 if struct!="Neutral":score+=1
 # Session score as a gating factor, not entry recommendation
 session_ok=london or ny
 qualifies=score>=6 and struct!="Neutral" and htb==struct and (sweepL or sweepH) and session_ok
 status="CONDITIONS ALIGN — VERIFY RETEST" if qualifies else "SETUP DEVELOPING — WAIT" if score>=3 else "WAIT / NO SETUP"
 zone=f"{fvg[0]:.5f} – {fvg[1]:.5f}" if fvg else f"{ob[0]:.5f} – {ob[1]:.5f}" if ob else "—"
 sl_note="SL sizing not calculated: broker pip/point and volatility settings required"
 news=news_gate()
 return f"""<b>G.SMART MONEY FX ✨ ULTRA PRO</b>
<b>{sym} | {tf}</b>
Status: <b>{status}</b>
Structure: {struct} | HTF ({htf}): {htb}
Confluence: {score}/9
Current price: <code>{px:.5f}</code>
Area to monitor: <code>{zone}</code>
Swing support: <code>{swingL:.5f}</code>
Swing resistance: <code>{swingH:.5f}</code>
Session: {session}
Checks: {', '.join(checks) if checks else '—'}
News: {news}
{sl_note}

<i>Experimental candidate scanner, not verified signals. Session hours are UTC approximations and do not account reliably for DST. Check an economic calendar manually; this bot has no live news feed.</i>""",qualifies
def commands(chat):
 send(chat,"<b>G.SMART MONEY FX ✨ ULTRA PRO</b>\n/analyze XAUUSD M15\n/market\n/pairs\n/monitor\n/stopmonitor\n/help\n\nMonitor only; no order execution.")
def handle(chat,text):
 a=text.strip().split();cmd=a[0].split("@")[0].lower()
 if cmd in ("/start","/help"):commands(chat)
 elif cmd=="/pairs":send(chat,"Pairs: "+", ".join(SYMS)+"\nTF: "+", ".join(TFS))
 elif cmd=="/analyze":
  s=a[1].upper() if len(a)>1 else "XAUUSD";t=a[2].upper() if len(a)>2 else "M15"
  try:send(chat,analyze(s,t if t in TFS else "M15")[0])
  except Exception as e:send(chat,"Analysis failed: "+str(e))
 elif cmd=="/market":
  lines=[]
  for s,p in SYMS.items():
   try:lines.append(s+": <code>"+str(float(candles(p,"15min",2)[-1]["close"]))+"</code>")
   except:lines.append(s+": unavailable")
  send(chat,"<b>Market M15</b>\n"+"\n".join(lines))
 elif cmd=="/monitor":monitor.add(chat);send(chat,"Monitoring enabled: M15 scans every 5 min; session gate and 60-min cooldown.")
 elif cmd=="/stopmonitor":monitor.discard(chat);send(chat,"Monitoring stopped.")
 else:send(chat,"Unknown command. /help")
def polling():
 global offset
 while True:
  try:
   j=requests.get(TG+"/getUpdates",params={"offset":offset,"timeout":25},timeout=30).json()
   for u in j.get("result",[]):
    offset=u["update_id"]+1;m=u.get("message",{})
    if m.get("text"):handle(m["chat"]["id"],m["text"])
  except Exception as e:print("poll",e);time.sleep(3)
def scanning():
 while True:
  for chat in list(monitor):
   for s in SYMS:
    k=f"{chat}:{s}";now=time.time()
    if now-last_alert.get(k,0)<3600:continue
    try:
     msg,ok=analyze(s,"M15")
     if ok:send(chat,msg);last_alert[k]=now
    except Exception as e:print("scan",e)
  time.sleep(300)
if __name__=="__main__":
 print("ULTRA PRO running");threading.Thread(target=scanning,daemon=True).start();polling()
