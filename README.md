# 🛡 AgentGuard
### AI Agent Wallet Security — Powered by Open Wallet Standard

> **"Don't give your AI agent the keys to the kingdom. Give it a leash."**

AgentGuard is an OWS Hackathon demo that solves one of the most critical unsolved problems in AI x Web3: **how do you let an AI agent use a blockchain wallet without giving it full, unrestricted access?**

Live Demo: [http://139.162.171.203:8501](http://139.162.171.203:8501) · Sepolia Testnet · Real transactions

---

## The Problem

Every major AI agent framework today — AutoGPT, LangChain, Claude agents — requires you to hand over a private key for blockchain operations. Once you do that:

- The agent can send **any amount** to **any address** at **any time**
- A single prompt injection or bug = **total loss of funds**
- There is **no audit trail**, no visibility, no way to stop it
- You have **no idea** what the agent did or why

This is not a hypothetical risk. It is happening today.

---

## The Solution: AgentGuard

AgentGuard wraps OWS (Open Wallet Standard) with a trust and governance layer, giving you **granular control** over what your AI agent can do with your wallet — without ever exposing your private key.

```
Master Wallet (you)
      │
      ▼
Policy Engine ──── "Max 0.5 ETH/day, only Sepolia, only these 5 addresses"
      │
      ▼
Sub-Agent API Key (SolanaTrader bot)
      │
      ▼
Human Approval Gate ──── "Approve this tx? y/n"
      │
      ▼
On-chain Transaction + Audit Log
      │
      ▼
Trust Score Dashboard (live, real-time)
```

---

## Why You Should Use AgentGuard

### 🔒 You never expose your private key
The agent gets a **scoped API key**, not your seed phrase. Even if the agent is compromised, the attacker can only do what the policy allows.

### 📋 Every action is logged and auditable
Every transaction attempt — approved or rejected — is written to the audit log with timestamp, reason, recipient, and amount. Full transparency.

### 📊 Trust Score tells you if your agent is behaving
The Trust Score (0–100) is computed from the agent's track record:
- Successful transactions → score goes up
- Policy violations / rejections → score goes down
- A score below 90 means your agent is misbehaving

### 🚫 Policy violations are blocked automatically
If the agent tries to:
- Send more than the daily limit
- Send to an address not on the allowlist
- Use a chain that's not permitted
- Interact with a blacklisted contract

AgentGuard **blocks it instantly** and logs the violation. No human intervention needed.

### 👁 Human-in-the-loop for high-stakes actions
For sensitive operations, AgentGuard requires explicit human approval before signing. The agent cannot bypass this gate.

### 🌐 Multi-chain from day one
One master wallet manages EVM (Ethereum, Base, Sepolia), Solana, Bitcoin, Cosmos, Tron, TON, and more — all through OWS.

---

## Why This Is Only Possible With OWS

Open Wallet Standard gives us three critical primitives out of the box that no other framework provides together:

1. **Multi-chain key derivation** — A single wallet derives and manages EVM, Solana, Bitcoin, Cosmos, and more from one mnemonic. No more managing separate wallets per chain.

2. **Scoped API keys with attached policies** — The wallet owner mints API keys that carry spending limits, chain allowlists, time bounds, and recipient allowlists. This is the core of AgentGuard's security model.

3. **Policy-enforced signing** — Agents sign transactions using their API token. The OWS runtime enforces the attached policy and rejects anything that violates it — before the transaction ever reaches the network.

Without OWS, building AgentGuard would require:
- Custom multi-chain wallet infrastructure
- A bespoke policy engine per chain
- Manual key management for each agent

OWS provides all of this out of the box. AgentGuard adds the missing trust, visibility, and governance layer on top.

---

## Live Demo Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AgentGuard Demo                       │
│                                                          │
│  Master Wallet: my-agent (OWS, encrypted)               │
│  EVM: 0x398F62F487a9138398B5fdE08e07beBA8698E804        │
│  Solana: DxC76E5V2iqrQovx6gQvmrHqUezBX8a5FzwLibDZ6jej  │
│                                                          │
│  Policy: agentguard-solana-base-expiry                   │
│  - Chain allowlist: Sepolia, Base                        │
│  - Spend limit: 0.5 ETH / 24h                           │
│  - Expiry: time-bound                                    │
│                                                          │
│  Sub-Agent: SolanaTrader                                 │
│  API Key: 2d96f0b4-d665-4d26-8e72-13f20c6b0d06          │
│                                                          │
│  Live Sepolia RPC: publicnode.com                        │
│  Tx History: Etherscan V2 API                            │
│  Dashboard: Streamlit (cyberpunk dark UI)                │
└─────────────────────────────────────────────────────────┘
```

---

## MVP Features

| Feature | Status |
|---|---|
| Master wallet (OWS, multi-chain) | ✅ |
| EVM + Solana address visibility | ✅ |
| Scoped sub-agent API key | ✅ |
| Policy with chain allowlist + expiry | ✅ |
| Human approval gate before signing | ✅ |
| Audit log with tx result tracking | ✅ |
| Trust score dashboard (real-time) | ✅ |
| Real Sepolia transactions (live) | ✅ |
| Policy violation detection + blocking | ✅ |
| Cyberpunk glassmorphic dashboard UI | ✅ |
| Auto-agent loop (continuous tx simulation) | ✅ |
| Rejected tx logging (separate from chain data) | ✅ |

---

## How to Run

### Prerequisites
- Linux server (Ubuntu 24 recommended)
- Python 3.12+
- OWS CLI installed

### Installation

```bash
# Clone the repo
git clone https://github.com/cemsid/agentguard.git
cd agentguard

# Install OWS
curl -fsSL https://docs.openwallet.sh/install.sh | bash
export PATH="/root/.ows/bin:$PATH"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create your wallet
ows wallet create --name "my-agent"

# Start the dashboard
streamlit run dashboard_app.py --server.address 0.0.0.0 --server.port 8501
```

### Running the Auto-Agent Loop

```bash
# Starts sending real Sepolia transactions + simulating policy violations
nohup ./auto_tx.sh >> data/tx.log 2>&1 &
```

### Configuration

Edit `dashboard_app.py` to set your:
- `EVM_ADDRESS` — your OWS wallet EVM address
- `ETHERSCAN_KEY` — your Etherscan API key (free at etherscan.io)
- `SEPOLIA_RPC` — your Sepolia RPC endpoint

---

## Project Structure

```
agentguard/
├── dashboard_app.py          # Main Streamlit dashboard
├── auto_tx.sh                # Auto-agent tx loop with policy simulation
├── scripts/
│   └── agent_loop.py         # Python agent loop
├── data/
│   ├── dashboard-data.json   # Wallet + delegation metadata
│   └── rejected-log.json     # Policy violation log (persistent)
├── policies/                 # OWS policy JSON files
├── requirements.txt
├── README.md
├── LOOM_SCRIPT.md
└── SUBMISSION.md
```

---

## Security Notes

- Never commit `.secrets/` or active OWS API tokens
- Rotate any token exposed in terminal history before submission
- The Etherscan API key in this repo is for demo purposes — rotate after hackathon
- Private keys are encrypted at rest by OWS vault (`~/.ows/`)
- The sub-agent **never** has access to the master wallet's mnemonic

---

## What's Next (Post-Hackathon Roadmap)

- **MetaMask integration** — connect existing wallets to AgentGuard policies
- **Multi-agent delegation trees** — agent A delegates to agent B with tighter constraints
- **EAS on-chain attestations** — every approved tx gets a blockchain attestation
- **Webhook alerts** — Slack/Telegram notification on policy violations
- **Web UI for policy management** — no-code policy builder
- **MoonPay onramp** — fund the master wallet directly from the dashboard

---

## Built With

- [Open Wallet Standard](https://github.com/open-wallet-standard/core) — wallet infrastructure
- [Streamlit](https://streamlit.io) — dashboard UI
- [web3.py](https://web3py.readthedocs.io) — Ethereum integration
- [Etherscan V2 API](https://docs.etherscan.io/v2-migration) — transaction history
- [publicnode.com](https://ethereum-sepolia-rpc.publicnode.com) — free Sepolia RPC

---

*Built at OWS Hackathon 2026 — AgentGuard by @cemsid*
