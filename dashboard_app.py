#!/usr/bin/env python3
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

DATA_PATH = Path("/opt/agentguard/data/dashboard-data.json")


st.set_page_config(
    page_title="AgentGuard",
    page_icon="shield",
    layout="wide",
)

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at top left, rgba(14,165,233,0.18), transparent 28%),
          radial-gradient(circle at top right, rgba(34,197,94,0.16), transparent 24%),
          linear-gradient(180deg, #07111f 0%, #0b172a 55%, #050b14 100%);
        color: #e5eef7;
      }
      .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1240px;
      }
      .card {
        background: rgba(8, 15, 28, 0.82);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 24px;
        padding: 20px 22px;
        box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
        backdrop-filter: blur(10px);
      }
      .eyebrow {
        color: #7dd3fc;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 12px;
        font-weight: 700;
      }
      .title {
        font-size: 40px;
        font-weight: 800;
        margin: 8px 0 4px 0;
      }
      .subtle {
        color: #94a3b8;
        font-size: 14px;
      }
      .mini-label {
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 11px;
        margin-bottom: 8px;
      }
      .big-value {
        font-size: 34px;
        font-weight: 800;
        line-height: 1.05;
      }
      .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        margin-right: 8px;
        margin-bottom: 8px;
        font-size: 12px;
        font-weight: 700;
        background: rgba(14,165,233,0.14);
        border: 1px solid rgba(125,211,252,0.24);
        color: #dbeafe;
      }
      .kv {
        margin: 8px 0;
        font-size: 14px;
      }
      .kv span {
        display: block;
        color: #94a3b8;
        font-size: 12px;
        margin-bottom: 2px;
      }
      .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 16px;
      }
      .stat {
        border-radius: 18px;
        padding: 14px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(148,163,184,0.12);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_data():
    if not DATA_PATH.exists():
        st.error(f"Missing data file: {DATA_PATH}")
        st.stop()
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_color(score: int) -> str:
    if score >= 80:
        return "#22c55e"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


def render_score_card(trust: dict):
    score = int(trust.get("score", 0))
    color = score_color(score)
    degrees = max(0, min(360, int(score * 3.6)))

    html = f"""
    <div class="card">
      <div class="eyebrow">Trust Score</div>
      <div style="display:flex; gap:24px; align-items:center; margin-top:12px;">
        <div style="
          width:190px; height:190px; border-radius:999px;
          background: conic-gradient({color} {degrees}deg, rgba(255,255,255,0.08) 0deg);
          display:flex; align-items:center; justify-content:center;
          box-shadow: inset 0 0 40px rgba(255,255,255,0.04), 0 16px 32px rgba(0,0,0,0.22);
        ">
          <div style="
            width:132px; height:132px; border-radius:999px;
            background:#07111f; border:1px solid rgba(148,163,184,0.16);
            display:flex; flex-direction:column; align-items:center; justify-content:center;
          ">
            <div style="font-size:46px; font-weight:800; line-height:1;">{score}</div>
            <div style="font-size:12px; color:#94a3b8;">out of 100</div>
          </div>
        </div>
        <div style="flex:1;">
          <div class="big-value">Delegated agent risk at a glance</div>
          <div class="subtle">Score rises with successful signed or sent transactions and falls on rejects or failures.</div>
          <div class="stat-grid">
            <div class="stat">
              <div class="mini-label">Successful</div>
              <div class="big-value">{trust.get("successfulTx", 0)}</div>
            </div>
            <div class="stat">
              <div class="mini-label">Rejected</div>
              <div class="big-value">{trust.get("rejectedTx", 0)}</div>
            </div>
            <div class="stat">
              <div class="mini-label">Failed</div>
              <div class="big-value">{trust.get("failedTx", 0)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_wallet_card(master: dict, sub_agent: dict):
    html = f"""
    <div class="card" style="height:100%;">
      <div class="eyebrow">Treasury Control</div>
      <div class="big-value" style="margin-top:10px;">{master.get("name", "-")}</div>
      <div class="subtle">Master wallet delegates tightly-scoped access to a sub-agent key.</div>

      <div style="margin-top:16px;">
        <div class="pill">Policy: {sub_agent.get("policy", "-")}</div>
        <div class="pill">Sub-Agent: {sub_agent.get("name", "-")}</div>
      </div>

      <div class="kv"><span>Wallet ID</span>{master.get("id", "-")}</div>
      <div class="kv"><span>Base / EVM</span>{master.get("evm", "-")}</div>
      <div class="kv"><span>Solana</span>{master.get("solana", "-")}</div>
      <div class="kv"><span>API Key ID</span>{sub_agent.get("apiKeyId", "-")}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_graph(master: dict, sub_agent: dict):
    html = f"""
    <html>
      <head>
        <style>
          body {{
            margin: 0;
            background: transparent;
            color: #e5eef7;
            font-family: Arial, sans-serif;
          }}
          .wrap {{
            display: flex;
            gap: 14px;
            align-items: center;
            overflow-x: auto;
            padding: 12px 4px 18px 4px;
          }}
          .node {{
            min-width: 190px;
            padding: 18px 16px;
            border-radius: 22px;
            background: linear-gradient(180deg, rgba(14,165,233,0.16), rgba(255,255,255,0.04));
            border: 1px solid rgba(125,211,252,0.18);
            box-shadow: 0 10px 30px rgba(0,0,0,0.22);
          }}
          .node .t {{
            font-size: 12px;
            color: #7dd3fc;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 8px;
            font-weight: 700;
          }}
          .node .v {{
            font-size: 20px;
            font-weight: 800;
            line-height: 1.15;
            margin-bottom: 6px;
          }}
          .node .s {{
            font-size: 12px;
            color: #cbd5e1;
            line-height: 1.45;
          }}
          .arrow {{
            font-size: 34px;
            color: #38bdf8;
            font-weight: 800;
            flex: 0 0 auto;
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="node">
            <div class="t">Master Wallet</div>
            <div class="v">{master.get("name", "-")}</div>
            <div class="s">{master.get("id", "-")}</div>
          </div>
          <div class="arrow">→</div>
          <div class="node">
            <div class="t">Scoped Policy</div>
            <div class="v">{sub_agent.get("policy", "-")}</div>
            <div class="s">allowed_chains + expires_at</div>
          </div>
          <div class="arrow">→</div>
          <div class="node">
            <div class="t">Sub-Agent</div>
            <div class="v">{sub_agent.get("name", "-")}</div>
            <div class="s">{sub_agent.get("apiKeyId", "-")}</div>
          </div>
          <div class="arrow">→</div>
          <div class="node">
            <div class="t">Approval Gate</div>
            <div class="v">Human in the loop</div>
            <div class="s">No signature before y/n approval</div>
          </div>
          <div class="arrow">→</div>
          <div class="node">
            <div class="t">Audit Layer</div>
            <div class="v">Trust score + log</div>
            <div class="s">Every tx decision is recorded</div>
          </div>
        </div>
      </body>
    </html>
    """
    components.html(html, height=230)


data = load_data()
trust = data.get("trustScore", {})
master = data.get("masterWallet", {})
sub_agent = data.get("subAgent", {})
audit_rows = data.get("auditLog", [])

st.markdown(
    f"""
    <div class="card" style="margin-bottom:18px;">
      <div class="eyebrow">OWS Hackathon Demo</div>
      <div class="title">AgentGuard</div>
      <div class="subtle">Delegated wallets, human approval, scoped policies, and transparent auditability.</div>
      <div class="subtle" style="margin-top:8px;">Last build: {data.get("generatedAt", "-")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.25, 1], gap="large")
with left:
    render_score_card(trust)
with right:
    render_wallet_card(master, sub_agent)

tab1, tab2, tab3 = st.tabs(["Overview", "Delegation Graph", "Audit Log"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Master Wallet", master.get("name", "-"))
    c2.metric("Sub-Agent", sub_agent.get("name", "-"))
    c3.metric("Policy", sub_agent.get("policy", "-"))

    st.markdown("### Chain Addresses")
    addr_df = pd.DataFrame(
        [
            {"Chain": "Base / EVM", "Address": master.get("evm", "-")},
            {"Chain": "Solana", "Address": master.get("solana", "-")},
        ]
    )
    st.dataframe(addr_df, use_container_width=True, hide_index=True)

with tab2:
    render_graph(master, sub_agent)
    with st.expander("Mermaid Source"):
        st.code(data.get("delegationGraph", {}).get("mermaid", ""), language="text")

with tab3:
    if audit_rows:
        df = pd.DataFrame(audit_rows)
        if "at" in df.columns:
            df = df.sort_values("at", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No audit rows yet.")
