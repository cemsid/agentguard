#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

AUDIT_PATH = Path("/opt/agentguard/data/audit-log.jsonl")
OUT_PATH = Path("/opt/agentguard/data/dashboard-data.json")

MASTER_WALLET = {
    "id": "82f41624-2d36-48a7-8930-4ebb0b14b757",
    "name": "my-agent",
    "evm": "0x398F62F487a9138398B5fdE08e07beBA8698E804",
    "solana": "DxC76E5V2iqrQovx6gQvmrHqUezBX8a5FzwLibDZ6jej",
}

SUB_AGENT = {
    "name": "SolanaTrader",
    "policy": "agentguard-solana-base-expiry",
    "apiKeyId": "2d96f0b4-d665-4d26-8e72-13f20c6b0d06",
}

def load_audit():
    if not AUDIT_PATH.exists():
        return []

    rows = []
    for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({
                "at": datetime.now(timezone.utc).isoformat(),
                "status": "parse_error",
                "raw": line,
            })
    return rows

def compute_trust_score(rows):
    success_count = sum(1 for r in rows if r.get("status") in {"signed", "sent", "attested"})
    rejected_count = sum(1 for r in rows if r.get("status") == "rejected")
    failed_count = sum(1 for r in rows if "failed" in str(r.get("status", "")) or r.get("status") == "error")

    score = min(100, success_count * 20)
    score = max(0, score - rejected_count * 2 - failed_count * 5)

    return {
        "score": score,
        "successfulTx": success_count,
        "rejectedTx": rejected_count,
        "failedTx": failed_count,
    }

def build_graph():
    mermaid = """graph TD
    A[Master Wallet: my-agent] --> B[Policy: agentguard-solana-base-expiry]
    B --> C[Sub-Agent API Key: SolanaTrader]
    C --> D[Human Approval Gate]
    D --> E[Base / Solana Transaction]
    E --> F[Audit Log + Trust Score]
"""
    return {
        "nodes": [
            {"id": "master", "label": "Master Wallet: my-agent"},
            {"id": "policy", "label": "Policy: agentguard-solana-base-expiry"},
            {"id": "subagent", "label": "Sub-Agent: SolanaTrader"},
            {"id": "approval", "label": "Human Approval Gate"},
            {"id": "chain", "label": "Base / Solana Tx"},
            {"id": "audit", "label": "Audit Log + Trust Score"},
        ],
        "edges": [
            {"from": "master", "to": "policy"},
            {"from": "policy", "to": "subagent"},
            {"from": "subagent", "to": "approval"},
            {"from": "approval", "to": "chain"},
            {"from": "chain", "to": "audit"},
        ],
        "mermaid": mermaid,
    }

def main():
    audit_rows = load_audit()
    trust = compute_trust_score(audit_rows)

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "project": "AgentGuard",
        "masterWallet": MASTER_WALLET,
        "subAgent": SUB_AGENT,
        "trustScore": trust,
        "auditLog": audit_rows,
        "delegationGraph": build_graph(),
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(payload["trustScore"], indent=2))

if __name__ == "__main__":
    main()
