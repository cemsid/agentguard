#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_PATH = Path("/opt/agentguard/data/audit-log.jsonl")

parser = argparse.ArgumentParser()
parser.add_argument("--wallet", required=True)
parser.add_argument("--chain", required=True)
parser.add_argument("--status", required=True)
parser.add_argument("--tx-hash", required=True)
parser.add_argument("--recipient", default=None)
parser.add_argument("--amount", default=None)
parser.add_argument("--reason", default=None)
parser.add_argument("--attestation-hash", default=None)
args = parser.parse_args()

entry = {
    "at": datetime.now(timezone.utc).isoformat(),
    "wallet": args.wallet,
    "chain": args.chain,
    "recipient": args.recipient,
    "amount": args.amount,
    "reason": args.reason,
    "status": args.status,
    "txHash": args.tx_hash,
    "attestationHash": args.attestation_hash,
}

AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
with AUDIT_PATH.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")

print(json.dumps(entry, indent=2))
