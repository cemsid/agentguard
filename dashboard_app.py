#!/usr/bin/env python3
import json
import math
from pathlib import Path
import requests
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

DATA_PATH = Path("/opt/agentguard/data/dashboard-data.json")

EVM_ADDRESS   = "0x398F62F487a9138398B5fdE08e07beBA8698E804"
SEPOLIA_RPC   = "https://ethereum-sepolia-rpc.publicnode.com"
ETHERSCAN_API = "https://api.etherscan.io/v2/api"
ETHERSCAN_KEY = "YOUR_ETHERSCAN_API_KEY_HERE"

@st.cache_data(ttl=60)
def fetch_sepolia_data():
    result = {"balance_eth": 0.0, "transactions": [], "tx_count": 0}
    try:
        r = requests.post(SEPOLIA_RPC, json={
            "jsonrpc":"2.0","method":"eth_getBalance",
            "params":[EVM_ADDRESS,"latest"],"id":1}, timeout=8)
        result["balance_eth"] = int(r.json().get("result","0x0"),16)/1e18
    except Exception: pass
    try:
        r = requests.get(ETHERSCAN_API, params={
            "module":"account","action":"txlist","address":EVM_ADDRESS,
            "startblock":0,"endblock":99999999,"sort":"desc",
            "apikey":ETHERSCAN_KEY,"offset":10000,"page":1,"chainid":"11155111"
        }, timeout=10)
        d = r.json()
        if d.get("status")=="1":
            result["transactions"] = d.get("result",[])
            result["tx_count"] = len(result["transactions"])
    except Exception: pass
    return result

def build_audit_log(txs):
    rows = []
    for tx in txs:
        ts = datetime.fromtimestamp(int(tx.get("timeStamp",0)),tz=timezone.utc)
        value_eth = int(tx.get("value",0))/1e18
        is_error  = tx.get("isError","0")=="1"
        status = "failed" if is_error else "signed"
        rows.append({
            "at": ts.isoformat(), "wallet":"my-agent","chain":"sepolia",
            "recipient": tx.get("to","-"), "amount": f"{value_eth:.4f} ETH",
            "reason": tx.get("functionName","Transfer")[:40] or "ETH Transfer",
            "status": status, "txHash": tx.get("hash",""),
        })
    return rows

def compute_trust_score(rows):
    succ = sum(1 for r in rows if r["status"] in ("signed","sent","attested"))
    rej  = sum(1 for r in rows if r["status"]=="rejected")
    fail = sum(1 for r in rows if "fail" in r["status"])
    total = succ+rej+fail
    return round(succ/total*100) if total>0 else 0, succ, rej, fail

def load_data():
    if not DATA_PATH.exists():
        st.error(f"Veri dosyası bulunamadı: {DATA_PATH}")
        st.stop()
    data = json.loads(DATA_PATH.read_text())
    sepolia = fetch_sepolia_data()
    if sepolia["transactions"]:
        real_rows = build_audit_log(sepolia["transactions"])
        # Ayrı dosyadaki rejected'ları da ekle
        import json as _json
        from pathlib import Path as _Path
        rej_file = _Path("/opt/agentguard/data/rejected-log.json")
        rejected_rows = _json.loads(rej_file.read_text()) if rej_file.exists() else []
        combined = real_rows + rejected_rows
        combined.sort(key=lambda x: x["at"], reverse=True)
        data["auditLog"] = combined
        score, succ, rej, fail = compute_trust_score(combined)
        data["trustScore"] = {"score": score, "successfulTx": succ, "rejectedTx": rej, "failedTx": fail}
    else:
        t = data.setdefault("trustScore",{})
        succ=int(t.get("successfulTx",0)); rej=int(t.get("rejectedTx",0)); fail=int(t.get("failedTx",0))
        if succ==0 and rej==0 and fail==0:
            for row in data.get("auditLog",[]):
                s=row.get("status","")
                if s in("signed","sent","attested"): succ+=1
                elif s=="rejected": rej+=1
                elif "fail" in s: fail+=1
            t["successfulTx"]=succ; t["rejectedTx"]=rej; t["failedTx"]=fail
        total=succ+rej+fail
        t["score"]=round(succ/total*100) if total>0 else 0
    data.setdefault("masterWallet",{})["balance"]=f"{sepolia['balance_eth']:.4f}"
    data["generatedAt"]=datetime.now(timezone.utc).isoformat()
    return data


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG + GLOBAL STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="AgentGuard", page_icon="🛡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family:'Inter',sans-serif !important; box-sizing:border-box; }
.stApp {
  background:
    radial-gradient(ellipse 90% 60% at 10% -10%, rgba(99,102,241,0.28) 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 90%  0%,  rgba(168,85,247,0.22) 0%, transparent 50%),
    radial-gradient(ellipse 50% 40% at 50% 100%, rgba(6,182,212,0.12)  0%, transparent 60%),
    linear-gradient(160deg,#02020D 0%,#080614 40%,#0D0920 70%,#02020D 100%) !important;
  color:#F1F5F9;
}
.block-container {
  padding-top:1.5rem !important; max-width:1440px !important;
  padding-left:2rem !important; padding-right:2rem !important;
}
#MainMenu,footer,header { visibility:hidden; }
.stTabs [data-baseweb="tab-list"] {
  background:rgba(255,255,255,0.03) !important;
  border-radius:16px !important; padding:5px !important;
  border:1px solid rgba(99,102,241,0.15) !important; gap:4px !important;
  backdrop-filter:blur(12px) !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius:12px !important; color:#475569 !important;
  font-weight:500 !important; font-size:13px !important;
  padding:9px 22px !important; transition:all .2s !important;
}
.stTabs [aria-selected="true"] {
  background:linear-gradient(135deg,#6366F1,#A855F7) !important;
  color:#fff !important; font-weight:600 !important;
  box-shadow:0 4px 24px rgba(99,102,241,0.45),0 0 0 1px rgba(99,102,241,0.3) !important;
}
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(99,102,241,0.4); border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# IFRAME HELPER
# ══════════════════════════════════════════════════════════════════════════════
def html(body: str, height: int, scrolling: bool = False):
    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:'Inter',sans-serif;color:#F1F5F9;overflow:{'auto' if scrolling else 'hidden'}}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(.75)}}}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}
@keyframes arcIn{{from{{stroke-dashoffset:var(--arc-len)}}to{{stroke-dashoffset:var(--arc-off)}}}}
@keyframes countUp{{from{{opacity:0;transform:scale(.8)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes glow{{0%,100%{{box-shadow:0 0 20px rgba(6,182,212,.25)}}50%{{box-shadow:0 0 45px rgba(6,182,212,.55)}}}}
</style>
</head><body>{body}</body></html>""", height=height, scrolling=scrolling)


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
def render_header(data):
    ts = data.get("generatedAt","")[:19].replace("T"," ")
    html(f"""
<div style="
  background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(168,85,247,0.05),rgba(6,182,212,0.03));
  border:1px solid rgba(99,102,241,0.2);border-radius:24px;padding:26px 36px;
  position:relative;overflow:hidden;animation:fadeUp .5s ease both;backdrop-filter:blur(20px);">
  <div style="position:absolute;top:-80px;left:-60px;width:320px;height:320px;
    background:radial-gradient(circle,rgba(99,102,241,0.15),transparent 70%);pointer-events:none;"></div>
  <div style="position:absolute;bottom:-60px;right:-40px;width:260px;height:260px;
    background:radial-gradient(circle,rgba(168,85,247,0.12),transparent 70%);pointer-events:none;"></div>
  <div style="position:absolute;inset:0;opacity:.03;pointer-events:none;
    background-image:linear-gradient(rgba(99,102,241,1) 1px,transparent 1px),
    linear-gradient(90deg,rgba(99,102,241,1) 1px,transparent 1px);
    background-size:40px 40px;"></div>
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;position:relative;z-index:1;">
    <div>
      <div style="display:inline-flex;align-items:center;gap:8px;
        background:linear-gradient(135deg,rgba(99,102,241,0.18),rgba(168,85,247,0.1));
        border:1px solid rgba(99,102,241,0.35);border-radius:999px;
        padding:5px 16px;margin-bottom:14px;backdrop-filter:blur(8px);">
        <div style="width:6px;height:6px;border-radius:50%;
          background:linear-gradient(135deg,#6366F1,#C084FC);
          box-shadow:0 0 8px rgba(99,102,241,0.9);"></div>
        <span style="color:#A5B4FC;font-size:10px;font-weight:700;letter-spacing:0.16em;">OWS HACKATHON DEMO · SEPOLIA TESTNET</span>
      </div>
      <div style="font-size:44px;font-weight:900;letter-spacing:-0.04em;line-height:1;margin-bottom:10px;
        font-family:'Syne',sans-serif;
        background:linear-gradient(135deg,#fff 0%,#C084FC 50%,#06B6D4 100%);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
        filter:drop-shadow(0 0 30px rgba(192,132,252,0.4));">
        🛡 AgentGuard
      </div>
      <div style="color:#475569;font-size:13.5px;max-width:560px;line-height:1.7;">
        Delegated wallets, human-in-the-loop approval, scoped policies
        and transparent auditability — powered by Open Wallet Standard.
      </div>
    </div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:12px;">
      <div style="background:linear-gradient(135deg,rgba(34,197,94,0.15),rgba(34,197,94,0.06));
        border:1px solid rgba(34,197,94,0.3);border-radius:999px;padding:8px 20px;
        display:inline-flex;align-items:center;gap:10px;
        box-shadow:0 0 32px rgba(34,197,94,0.2);">
        <div style="width:8px;height:8px;border-radius:50%;background:#22C55E;
          box-shadow:0 0 10px #22C55E,0 0 24px rgba(34,197,94,0.8);
          animation:pulse 2s ease-in-out infinite;"></div>
        <span style="color:#86EFAC;font-size:12px;font-weight:700;letter-spacing:0.14em;">LIVE · SEPOLIA</span>
      </div>
      <div style="color:#1E293B;font-size:11px;">Last sync: <span style="color:#334155;font-family:monospace;">{ts} UTC</span></div>
    </div>
  </div>
</div>
""", height=178)


# ══════════════════════════════════════════════════════════════════════════════
# TRUST SCORE
# ══════════════════════════════════════════════════════════════════════════════
def render_trust_score(trust):
    score = int(trust.get("score",0))
    succ  = int(trust.get("successfulTx",0))
    rej   = int(trust.get("rejectedTx",0))
    fail  = int(trust.get("failedTx",0))

    R=108; cx=145; cy=148
    full=math.pi*R; off=full*(1-score/100)

    if score>=75:   c1,c2,glow,lc="#22C55E","#06B6D4","rgba(34,197,94,0.35)","#22C55E"
    elif score>=40: c1,c2,glow,lc="#F59E0B","#EF4444","rgba(245,158,11,0.35)","#F59E0B"
    else:           c1,c2,glow,lc="#EF4444","#7F1D1D","rgba(239,68,68,0.35)","#EF4444"

    def stat(val,label,col,icon):
        return f"""<div style="flex:1;background:linear-gradient(145deg,rgba(255,255,255,.03),rgba(255,255,255,.01));
          border:1px solid {col}22;border-radius:16px;padding:16px 12px;text-align:center;
          position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;"
          onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 12px 32px rgba(0,0,0,.4),0 0 20px {col}30'"
          onmouseout="this.style.transform='';this.style.boxShadow=''">
          <div style="position:absolute;top:-20px;left:50%;transform:translateX(-50%);
            width:80px;height:80px;background:radial-gradient(circle,{col}18,transparent 70%);pointer-events:none;"></div>
          <div style="font-size:14px;margin-bottom:8px;">{icon}</div>
          <div style="font-size:30px;font-weight:800;color:{col};font-family:'Syne',sans-serif;
            line-height:1;margin-bottom:6px;text-shadow:0 0 20px {col}80;">{val}</div>
          <div style="font-size:9px;color:#334155;font-weight:700;text-transform:uppercase;letter-spacing:.12em;">{label}</div>
        </div>"""

    html(f"""
<div style="background:linear-gradient(145deg,rgba(99,102,241,0.07),rgba(168,85,247,0.04),rgba(6,182,212,0.03));
  border:1px solid rgba(99,102,241,0.18);border-radius:24px;padding:28px 26px;
  animation:fadeUp .6s ease both;backdrop-filter:blur(16px);position:relative;overflow:hidden;">
  <div style="position:absolute;top:-40px;right:-40px;width:200px;height:200px;
    background:radial-gradient(circle,{glow},transparent 70%);pointer-events:none;opacity:.7;"></div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
    <div style="width:36px;height:36px;border-radius:12px;
      background:linear-gradient(135deg,rgba(99,102,241,0.3),rgba(168,85,247,0.2));
      border:1px solid rgba(99,102,241,0.4);display:flex;align-items:center;justify-content:center;
      font-size:16px;box-shadow:0 0 20px rgba(99,102,241,0.3);">🛡</div>
    <span style="color:#64748B;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.16em;">Delegation Safety Score</span>
  </div>
  <div style="display:flex;align-items:center;gap:28px;flex-wrap:wrap;">
    <div style="position:relative;flex-shrink:0;animation:float 4s ease-in-out infinite;">
      <svg width="{cx*2}" height="{cy}" viewBox="0 0 {cx*2} {cy}" style="overflow:visible;filter:drop-shadow(0 0 24px {glow});">
        <defs>
          <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>
          </linearGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          <filter id="glow2"><feGaussianBlur stdDeviation="12" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>
        <path d="M {cx-R},{cy} A {R},{R} 0 0,1 {cx+R},{cy}"
          fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="16" stroke-linecap="round"/>
        <path d="M {cx-R},{cy} A {R},{R} 0 0,1 {cx+R},{cy}"
          fill="none" stroke="url(#g2)" stroke-width="16" stroke-linecap="round"
          stroke-dasharray="{full:.2f}" stroke-dashoffset="{off:.2f}" filter="url(#glow2)" opacity=".45"/>
        <path d="M {cx-R},{cy} A {R},{R} 0 0,1 {cx+R},{cy}"
          fill="none" stroke="url(#g2)" stroke-width="14" stroke-linecap="round"
          stroke-dasharray="{full:.2f}" stroke-dashoffset="{off:.2f}" filter="url(#glow)"
          style="animation:arcIn 1.4s cubic-bezier(.4,0,.2,1) both;--arc-len:{full:.2f};--arc-off:{off:.2f};"/>
        <text x="{cx}" y="{cy-26}" text-anchor="middle" font-size="60" font-weight="900"
          fill="{lc}" font-family="'Syne',sans-serif" filter="url(#glow)"
          style="animation:countUp .8s ease both;">{score}</text>
        <text x="{cx}" y="{cy-6}" text-anchor="middle" font-size="13" fill="#334155" font-weight="600">/100</text>
        <text x="{cx}" y="{cy+16}" text-anchor="middle" font-size="11" fill="{lc}"
          font-weight="700" letter-spacing=".12em">Agent Safety</text>
      </svg>
    </div>
    <div style="flex:1;min-width:200px;">
      <div style="color:#4B5563;font-size:12px;line-height:1.7;margin-bottom:16px;">
        Score rises with successful txs,<br>falls on rejections and failures.
      </div>
      <div style="display:flex;gap:10px;">
        {stat(succ,"Success","#22C55E","✅")}
        {stat(rej,"Rejected","#EF4444","🚫")}
        {stat(fail,"Failed","#F59E0B","⚠️")}
      </div>
    </div>
  </div>
</div>
""", height=310)


# ══════════════════════════════════════════════════════════════════════════════
# WALLET CARD
# ══════════════════════════════════════════════════════════════════════════════
def render_wallet_card(master, sub_agent):
    balance = master.get("balance","0.0000")
    try:    usd = float(balance)*3200
    except: usd = 0.0

    def kv(icon,label,val):
        short = val if len(val)<22 else val[:18]+"…"
        return f"""<div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.05);
          border-radius:14px;padding:11px 14px;display:flex;align-items:center;gap:12px;margin-bottom:8px;
          transition:border-color .2s,background .2s;"
          onmouseover="this.style.borderColor='rgba(99,102,241,.35)';this.style.background='rgba(99,102,241,.06)'"
          onmouseout="this.style.borderColor='rgba(255,255,255,.05)';this.style.background='rgba(255,255,255,.025)'">
          <div style="width:32px;height:32px;border-radius:10px;flex-shrink:0;
            background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25);
            display:flex;align-items:center;justify-content:center;font-size:14px;">{icon}</div>
          <div style="flex:1;min-width:0;">
            <div style="color:#1E293B;font-size:9px;font-weight:700;text-transform:uppercase;
              letter-spacing:.1em;margin-bottom:3px;">{label}</div>
            <div style="color:#64748B;font-size:11px;font-weight:500;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{val}">{short}</div>
          </div>
          <button onclick="navigator.clipboard.writeText('{val}')"
            style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);
            border-radius:8px;color:#818CF8;font-size:10px;font-weight:600;
            padding:5px 10px;cursor:pointer;transition:all .2s;white-space:nowrap;"
            onmouseover="this.style.background='rgba(99,102,241,.3)';this.style.boxShadow='0 0 14px rgba(99,102,241,.5)'"
            onmouseout="this.style.background='rgba(99,102,241,.12)';this.style.boxShadow=''">Copy</button>
        </div>"""

    html(f"""
<div style="background:linear-gradient(145deg,rgba(99,102,241,0.08),rgba(168,85,247,0.05));
  border:1px solid rgba(99,102,241,0.2);border-radius:24px;padding:26px 24px;
  animation:fadeUp .65s ease both;backdrop-filter:blur(16px);position:relative;overflow:hidden;">
  <div style="position:absolute;top:-60px;right:-60px;width:220px;height:220px;
    background:radial-gradient(circle,rgba(168,85,247,.18),transparent 70%);pointer-events:none;"></div>
  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;gap:12px;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:40px;height:40px;border-radius:13px;
        background:linear-gradient(135deg,rgba(99,102,241,.35),rgba(168,85,247,.25));
        border:1px solid rgba(99,102,241,.45);display:flex;align-items:center;
        justify-content:center;font-size:18px;box-shadow:0 0 24px rgba(99,102,241,.35);">🏦</div>
      <div>
        <div style="color:#1E293B;font-size:9px;font-weight:700;
          text-transform:uppercase;letter-spacing:.14em;margin-bottom:4px;">Treasury Control</div>
        <div style="font-size:16px;font-weight:800;font-family:'Syne',sans-serif;
          background:linear-gradient(135deg,#F1F5F9,#C084FC);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
          Master Wallet: {master.get("name","-")}</div>
      </div>
    </div>
  </div>
  <!-- HERO BALANCE -->
  <div style="background:linear-gradient(135deg,rgba(6,182,212,0.1),rgba(99,102,241,0.08),rgba(168,85,247,0.06));
    border:1px solid rgba(6,182,212,0.25);border-radius:18px;padding:20px 22px;margin-bottom:18px;
    position:relative;overflow:hidden;animation:glow 3s ease-in-out infinite;">
    <div style="position:absolute;top:8px;right:14px;font-size:22px;opacity:.35;animation:float 3s ease-in-out infinite;">✦</div>
    <div style="position:absolute;top:32px;right:42px;font-size:13px;opacity:.2;animation:float 4s ease-in-out infinite .5s;">✦</div>
    <div style="position:absolute;bottom:10px;right:22px;font-size:9px;opacity:.15;animation:float 3.5s ease-in-out infinite 1s;">✦</div>
    <div style="color:#0891B2;font-size:10px;font-weight:700;text-transform:uppercase;
      letter-spacing:.14em;margin-bottom:8px;">⟠ Sepolia Balance</div>
    <div style="font-size:46px;font-weight:900;font-family:'Syne',sans-serif;line-height:1;
      background:linear-gradient(135deg,#67E8F9,#06B6D4,#818CF8);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
      filter:drop-shadow(0 0 20px rgba(6,182,212,0.5));margin-bottom:6px;">
      {balance} <span style="font-size:20px;opacity:.7;">ETH</span>
    </div>
    <div style="color:#164E63;font-size:13px;font-weight:500;">
      ≈ <span style="color:#0E7490;font-weight:600;">${usd:,.2f} USD</span>
      <span style="color:#1E293B;font-size:11px;margin-left:8px;">· testnet</span>
    </div>
  </div>
  <!-- badges -->
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">
    <div style="background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);
      border-radius:999px;padding:6px 14px;display:flex;align-items:center;gap:6px;">
      <span style="font-size:11px;">⚙️</span>
      <span style="color:#A5B4FC;font-size:11px;font-weight:600;">{sub_agent.get("policy","-")}</span>
    </div>
    <div style="background:rgba(168,85,247,.15);border:1px solid rgba(168,85,247,.3);
      border-radius:999px;padding:6px 14px;display:flex;align-items:center;gap:6px;">
      <span style="font-size:11px;">🤖</span>
      <span style="color:#DDD6FE;font-size:11px;font-weight:600;">{sub_agent.get("name","-")}</span>
    </div>
  </div>
  {kv("🔑","Wallet ID",master.get("id","-"))}
  {kv("⛓️","Base / EVM",master.get("evm","-"))}
  {kv("◎","Solana",master.get("solana","-"))}
</div>
""", height=430)


# ══════════════════════════════════════════════════════════════════════════════
# DELEGATION GRAPH
# ══════════════════════════════════════════════════════════════════════════════
def render_graph(master, sub_agent):
    nodes=[
        ("👑","MASTER WALLET", master.get("name","-"),     master.get("id","-")[:18]+"…",         "#6366F1","#818CF8"),
        ("🔒","SCOPED POLICY", sub_agent.get("policy","-"),"allowed_chains · expires_at",          "#A855F7","#C084FC"),
        ("🤖","SUB-AGENT",     sub_agent.get("name","-"),  sub_agent.get("apiKeyId","-")[:18]+"…", "#06B6D4","#67E8F9"),
        ("🧑","APPROVAL GATE","Human-in-the-Loop",         "Manual sign-off required",             "#10B981","#34D399"),
        ("📋","AUDIT LAYER",  "Trust Score + Log",         "Every tx is recorded",                 "#F59E0B","#FCD34D"),
    ]
    cards=""
    for i,(icon,label,title,sub,cm,cl) in enumerate(nodes):
        cards+=f"""
        <div style="min-width:190px;max-width:200px;flex-shrink:0;
          background:linear-gradient(160deg,rgba(10,8,24,.98),rgba(18,14,36,.96));
          border:1px solid {cm}28;border-top:2px solid {cm};border-radius:20px;
          padding:22px 18px;position:relative;overflow:hidden;
          box-shadow:0 10px 40px rgba(0,0,0,.5),0 0 0 1px {cm}10;
          cursor:default;transition:transform .25s,box-shadow .25s;"
          onmouseover="this.style.transform='translateY(-8px) scale(1.03)';this.style.boxShadow='0 24px 60px rgba(0,0,0,.6),0 0 40px {cm}40'"
          onmouseout="this.style.transform='';this.style.boxShadow='0 10px 40px rgba(0,0,0,.5)'">
          <div style="position:absolute;top:-30px;right:-30px;width:100px;height:100px;
            background:radial-gradient(circle,{cm}25,transparent 70%);pointer-events:none;"></div>
          <div style="font-size:26px;margin-bottom:14px;filter:drop-shadow(0 2px 12px {cm}90);
            animation:float {2.5+i*0.3:.1f}s ease-in-out infinite;">{icon}</div>
          <div style="font-size:8px;font-weight:800;letter-spacing:.18em;
            text-transform:uppercase;color:{cl};margin-bottom:10px;">{label}</div>
          <div style="font-size:13px;font-weight:700;color:#F1F5F9;
            line-height:1.3;margin-bottom:8px;font-family:'Syne',sans-serif;">{title}</div>
          <div style="font-size:10px;color:#334155;line-height:1.6;">{sub}</div>
        </div>"""
        if i<len(nodes)-1:
            nc=nodes[i+1][4]
            cards+=f"""
            <div style="display:flex;align-items:center;flex-shrink:0;padding:0 2px;margin-top:30px;">
              <div style="position:relative;width:48px;height:3px;
                background:linear-gradient(90deg,{cm},{nc});border-radius:2px;
                box-shadow:0 0 16px {cm}80,0 0 32px {nc}50;">
                <div style="position:absolute;right:-10px;top:50%;transform:translateY(-50%);
                  width:0;height:0;border-left:12px solid {nc};
                  border-top:7px solid transparent;border-bottom:7px solid transparent;
                  filter:drop-shadow(0 0 8px {nc});"></div>
              </div>
            </div>"""

    html(f"""
<div style="display:flex;align-items:flex-start;gap:2px;padding:20px 12px 28px;min-width:max-content;">
  {cards}
</div>""", height=264, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
def render_overview(master, sub_agent):
    items=[
        ("🏦","Master Wallet",  master.get("name","-"),           "#6366F1"),
        ("🤖","Sub-Agent",      sub_agent.get("name","-"),        "#A855F7"),
        ("📜","Active Policy",  sub_agent.get("policy","-"),      "#06B6D4"),
        ("⟠","Sepolia Balance", master.get("balance","0")+" ETH", "#22C55E"),
    ]
    cards="".join(f"""
    <div style="background:linear-gradient(145deg,rgba(255,255,255,.03),rgba(255,255,255,.01));
      border:1px solid {c}20;border-left:3px solid {c}80;border-radius:16px;padding:20px 18px;
      transition:transform .2s,box-shadow .2s,border-color .2s;"
      onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 12px 36px rgba(0,0,0,.4),0 0 20px {c}30'"
      onmouseout="this.style.transform='';this.style.boxShadow=''">
      <div style="font-size:22px;margin-bottom:12px;filter:drop-shadow(0 2px 8px {c}60);">{ic}</div>
      <div style="color:#1E293B;font-size:9px;font-weight:700;text-transform:uppercase;
        letter-spacing:.12em;margin-bottom:7px;">{lb}</div>
      <div style="color:#E2E8F0;font-size:15px;font-weight:700;font-family:'Syne',sans-serif;">{v}</div>
    </div>""" for ic,lb,v,c in items)

    html(f"""
<div style="background:rgba(99,102,241,0.04);border:1px solid rgba(99,102,241,0.12);
  border-radius:20px;padding:24px;backdrop-filter:blur(8px);">
  <div style="color:#334155;font-size:10px;font-weight:700;text-transform:uppercase;
    letter-spacing:.14em;margin-bottom:18px;">Wallet Overview · Sepolia Testnet</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;">{cards}</div>
</div>""", height=190)


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT LOG — custom HTML table
# ══════════════════════════════════════════════════════════════════════════════
def render_audit_log(audit_rows):
    if not audit_rows:
        html("""<div style="text-align:center;padding:60px;color:#1E293B;
          border:1px dashed rgba(99,102,241,0.2);border-radius:20px;">
          <div style="font-size:36px;margin-bottom:14px;">📭</div>
          <div style="font-size:14px;font-weight:500;">No audit entries yet.</div>
        </div>""", height=200)
        return

    rows_html=""
    for i,row in enumerate(sorted(audit_rows,key=lambda x:x.get("at",""),reverse=True)[:30]):
        st_val=row.get("status","")
        if st_val in("signed","sent","attested"): sc,sb="#22C55E","rgba(34,197,94,0.12)"
        elif st_val=="rejected":                  sc,sb="#EF4444","rgba(239,68,68,0.12)"
        else:                                     sc,sb="#F59E0B","rgba(245,158,11,0.12)"
        at   = row.get("at","")[:19].replace("T"," ")
        rcpt = row.get("recipient","-")
        rcpt_s = rcpt[:10]+"…"+rcpt[-6:] if len(rcpt)>20 else rcpt
        txh  = row.get("txHash","") or ""
        txh_s= txh[:8]+"…"+txh[-6:] if len(txh)>18 else (txh if txh else "—")
        txh_url = f"https://sepolia.etherscan.io/tx/{txh}" if txh else "#"
        amt  = row.get("amount","-")
        rsn  = row.get("reason","-")[:28]
        bg   = "rgba(255,255,255,0.015)" if i%2==0 else "transparent"

        rows_html+=f"""
        <tr style="background:{bg};border-bottom:1px solid rgba(255,255,255,0.04);transition:background .15s;"
          onmouseover="this.style.background='rgba(99,102,241,0.08)'"
          onmouseout="this.style.background='{bg}'">
          <td style="padding:12px 14px;color:#334155;font-size:11px;white-space:nowrap;font-family:monospace;">{at}</td>
          <td style="padding:12px 14px;">
            <span style="background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.25);
              border-radius:6px;padding:3px 9px;color:#A5B4FC;font-weight:600;font-size:10px;">my-agent</span>
          </td>
          <td style="padding:12px 14px;">
            <span style="background:rgba(6,182,212,.1);border:1px solid rgba(6,182,212,.2);
              border-radius:6px;padding:3px 9px;color:#67E8F9;font-weight:600;font-size:10px;">sepolia</span>
          </td>
          <td style="padding:12px 14px;color:#475569;font-size:11px;font-family:monospace;" title="{rcpt}">{rcpt_s}</td>
          <td style="padding:12px 14px;color:#E2E8F0;font-size:11px;font-weight:600;">{amt}</td>
          <td style="padding:12px 14px;color:#334155;font-size:11px;">{rsn}</td>
          <td style="padding:12px 14px;">
            <span style="background:{sb};border:1px solid {sc}40;border-radius:999px;
              padding:4px 12px;color:{sc};font-size:10px;font-weight:700;">{st_val}</span>
          </td>
          <td style="padding:12px 14px;">
            <a href="{txh_url}" target="_blank"
              style="color:#6366F1;font-size:10px;font-family:monospace;text-decoration:none;
              background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.2);
              border-radius:6px;padding:3px 9px;transition:all .2s;"
              onmouseover="this.style.background='rgba(99,102,241,.28)';this.style.boxShadow='0 0 12px rgba(99,102,241,.4)'"
              onmouseout="this.style.background='rgba(99,102,241,.1)';this.style.boxShadow=''"
              >{txh_s if txh_s else "—"}</a>
          </td>
        </tr>"""

    n=len(audit_rows[:30])
    html(f"""
<div style="background:rgba(255,255,255,.02);border:1px solid rgba(99,102,241,.15);
  border-radius:20px;overflow:hidden;backdrop-filter:blur(12px);">
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr style="background:rgba(99,102,241,0.1);border-bottom:1px solid rgba(99,102,241,.2);">
        {''.join(f'<th style="padding:12px 14px;text-align:left;color:#334155;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;">{h}</th>' for h in ["Timestamp","Wallet","Chain","Recipient","Amount","Reason","Status","Tx Hash"])}
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", height=min(80+n*46,680), scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
data      = load_data()
trust     = data.get("trustScore",{})
master    = data.get("masterWallet",{})
sub_agent = data.get("subAgent",{})
audit_rows= data.get("auditLog",[])

render_header(data)
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

col1,col2=st.columns([1.5,1],gap="large")
with col1: render_trust_score(trust)
with col2: render_wallet_card(master,sub_agent)

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
tab1,tab2,tab3=st.tabs(["📊  Overview","🔗  Delegation Graph","📋  Audit Log"])

with tab1:
    render_overview(master,sub_agent)
    st.markdown("<div style='color:#1E293B;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;margin:16px 0 8px 2px;'>Chain Addresses</div>",unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([
        {"Chain":"Base / EVM (Sepolia)","Address":master.get("evm","-")},
        {"Chain":"Solana",              "Address":master.get("solana","-")},
    ]),use_container_width=True,hide_index=True)

with tab2:
    render_graph(master,sub_agent)

with tab3:
    st.markdown(f"""<div style="margin-bottom:14px;">
      <a href="https://sepolia.etherscan.io/address/{EVM_ADDRESS}" target="_blank"
        style="color:#818CF8;font-size:12px;text-decoration:none;
        background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
        border-radius:10px;padding:7px 16px;display:inline-flex;align-items:center;gap:7px;">
        🔍 View on Sepolia Etherscan ↗
      </a></div>""",unsafe_allow_html=True)
    render_audit_log(audit_rows)
