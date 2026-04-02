#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUEST_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/opt/agentguard/data/pending-tx.json")
TOKEN_PATH = Path(os.environ.get("AGENT_TOKEN_FILE", "/opt/agentguard/.secrets/solana_trader.key"))
AUDIT_PATH = Path("/opt/agentguard/data/audit-log.jsonl")


def append_audit(entry: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def fail(message: str, extra: dict | None = None, code: int = 1) -> int:
    payload = {
        "at": datetime.now(timezone.utc).isoformat(),
        "status": "error",
        "message": message,
    }
    if extra:
        payload.update(extra)
    append_audit(payload)
    print(f"error: {message}", file=sys.stderr)
    return code


def main() -> int:
    if not REQUEST_PATH.exists():
        return fail(f"request file not found: {REQUEST_PATH}")

    if not TOKEN_PATH.exists():
        return fail(f"token file not found: {TOKEN_PATH}")

    with REQUEST_PATH.open("r", encoding="utf-8") as f:
        req = json.load(f)

    token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    if not token.startswith("ows_key_"):
        return fail("token file does not contain a valid ows_key_ token")

    wallet = req.get("wallet")
    chain = req.get("chain")
    tx_hex = req.get("txHex")

    if not wallet or not chain or not tx_hex:
        return fail("request file must contain wallet, chain, and txHex")

    print("\n=== AgentGuard Approval ===")
    print(f"Wallet:    {wallet}")
    print(f"Chain:     {chain}")
    print(f"Recipient: {req.get('recipient', '-')}")
    print(f"Amount:    {req.get('amount', '-')}")
    print(f"Reason:    {req.get('reason', '-')}")
    print(f"TX Hex:    {str(tx_hex)[:66]}{'...' if len(str(tx_hex)) > 66 else ''}")

    answer = input("Bu tx'i onaylıyor musun? (y/n): ").strip().lower()

    audit_base = {
        "at": datetime.now(timezone.utc).isoformat(),
        "wallet": wallet,
        "chain": chain,
        "recipient": req.get("recipient"),
        "amount": req.get("amount"),
        "reason": req.get("reason"),
        "txHex": tx_hex,
    }

    if answer != "y":
        append_audit({**audit_base, "status": "rejected"})
        print("Rejected. Tx imzalanmadi.")
        return 1

    env = os.environ.copy()
    env["PATH"] = f"/root/.ows/bin:{env.get('PATH', '')}"
    env["OWS_PASSPHRASE"] = token

    cmd = [
        "ows",
        "sign",
        "tx",
        "--wallet",
        wallet,
        "--chain",
        chain,
        "--tx",
        tx_hex,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        append_audit({
            **audit_base,
            "status": "sign_failed",
            "stderr": result.stderr.strip(),
            "stdout": result.stdout.strip(),
        })
        print(result.stderr.strip() or result.stdout.strip(), file=sys.stderr)
        return result.returncode

    append_audit({
        **audit_base,
        "status": "signed",
        "ows_output": result.stdout.strip(),
    })

    print("Approved and signed.")
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
