# AgentGuard

AgentGuard is an OWS hackathon demo that lets a master treasury wallet delegate tightly-scoped signing power to a sub-agent, while keeping a human approval checkpoint and a transparent audit trail.

## Why this is possible with OWS

Open Wallet Standard makes this demo possible because it gives us three critical primitives out of the box:

1. A single wallet can derive and manage multi-chain accounts like EVM and Solana.
2. The owner can mint scoped API keys with attached policies for agent access.
3. Agents can sign with an API token instead of the wallet owner's passphrase, while policies restrict what they are allowed to do.

That means AgentGuard does not need to reinvent wallet delegation. OWS already provides the foundation for safe wallet programmability, and AgentGuard adds the missing trust layer on top:
- human-in-the-loop approval
- audit logging
- trust score visualization
- delegation graph visibility

## MVP Features

- Master wallet treasury using OWS
- EVM + Solana address visibility
- Scoped sub-agent API key
- Policy with chain allowlist and expiry
- Human approval gate before signing
- Audit log with tx result tracking
- Trust score dashboard in Streamlit

## Current Demo Setup

- Master wallet: `my-agent`
- Master wallet ID: `82f41624-2d36-48a7-8930-4ebb0b14b757`
- Sub-agent: `SolanaTrader`
- Policy: `agentguard-solana-base-expiry`

## How to Run

1. Activate the environment:
   source /opt/agentguard/.venv/bin/activate

2. Add OWS to PATH:
   export PATH="/root/.ows/bin:$PATH"

3. Rebuild dashboard data:
   python3 /opt/agentguard/scripts/build_dashboard_data.py

4. Start the dashboard:
   streamlit run /opt/agentguard/dashboard_app.py --server.address 0.0.0.0 --server.port 8501

Open:
- http://139.162.171.203:8501

## Demo Notes

- Human approval is required before signing.
- Every decision is written to the audit log.
- Trust score is computed from successful, rejected, and failed actions.
- For the MVP, tx hash logging is used as the minimum attestation fallback.

## Security Note

Do not commit .secrets/ or active OWS API tokens.
Rotate any token that was exposed in terminal history or chat before submission.
