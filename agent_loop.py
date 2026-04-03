#!/usr/bin/env python3
import json
import random
import time
import subprocess
import sys
import secrets
from datetime import datetime, timezone
from pathlib import Path

AUDIT_PATH   = Path("/opt/agentguard/data/audit-log.jsonl")
BUILD_SCRIPT = Path("/opt/agentguard/scripts/build_dashboard_data.py")
PYTHON       = sys.executable
INTERVAL     = 30

CHAINS = ["base", "solana"]

RECIPIENTS = [
    "0x398F62F487a9138398B5fdE08e07beBA8698E804",
    "DxC76E5V2iqrQovx6gQvmrHqUezBX8a5FzwLibDZ6jej",
    "0xDeadBeef1234567890abcdef1234567890abcdef",
    "0xAbc123Def456789012345678901234567890abcd",
]

REASONS = [
    "Automated trade execution",
    "Policy-scoped payment",
    "Sub-agent swap request",
    "Cross-chain transfer",
    "DeFi yield claim",
    "Liquidity provision",
    "Hackathon demo tx",
]

AMOUNTS = [
    "0.01 ETH",
    "0.05 ETH",
    "0.02 ETH",
    "0.1 SOL",
    "0.25 SOL",
    "0.5 SOL",
]

OUTCOMES = [
    "signed",
    "signed",
    "signed",
    "signed",
    "signed",
    "signed",
    "signed",
    "rejected",
    "rejected",
    "sign_failed",
]


def fake_hash():
    return "0x" + secrets.token_hex(32)


def append_audit(entry):
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def rebuild():
    r = subprocess.run(
        [PYTHON, str(BUILD_SCRIPT)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print("BUILD ERR: " + r.stderr[:120])
    else:
        print("  dashboard rebuilt ok")


def simulate():
    chain   = random.choice(CHAINS)
    outcome = random.choice(OUTCOMES)

    entry = {
        "at":              datetime.now(timezone.utc).isoformat(),
        "wallet":          "my-agent",
        "chain":           chain,
        "recipient":       random.choice(RECIPIENTS),
        "amount":          random.choice(AMOUNTS),
        "reason":          random.choice(REASONS),
        "status":          outcome,
        "txHash":          fake_hash() if outcome == "signed" else None,
        "attestationHash": None,
    }

    append_audit(entry)

    icon = "OK" if outcome == "signed" else ("NO" if outcome == "rejected" else "ERR")
    print(icon + " | " + entry["at"] + " | " + chain + " | " + outcome + " | " + entry["amount"])

    rebuild()


if __name__ == "__main__":
    print("AgentGuard loop started — interval " + str(INTERVAL) + "s")
    rebuild()
    while True:
        simulate()
        time.sleep(INTERVAL)
