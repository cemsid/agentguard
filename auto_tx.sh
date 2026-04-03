#!/bin/bash

WALLET="my-agent"
PASSWORD=""
RPC="https://ethereum-sepolia-rpc.publicnode.com"
FROM="0x398F62F487a9138398B5fdE08e07beBA8698E804"

# Gerçekçi test adresleri
ADDRESSES=(
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"
    "0x4675C7e5BaAFBFFbca748158bEcBA61ef3b0a263"
    "0xE853c56864A2ebe4576a807D26Fdc4A0adA51919"
)

send_tx() {
    local TO=$1
    HEX=$(/opt/agentguard/.venv/bin/python3 << PYEOF
from web3 import Web3
import rlp
w3 = Web3(Web3.HTTPProvider("$RPC"))
nonce    = w3.eth.get_transaction_count("$FROM", "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
tip      = w3.to_wei(2, "gwei")
max_fee  = base_fee + tip
payload  = rlp.encode([11155111, nonce, tip, max_fee, 21000,
    bytes.fromhex("$TO"[2:]), w3.to_wei(0.0001, "ether"), b"", []])
print("02" + payload.hex())
PYEOF
)
    RESULT=$(echo "$PASSWORD" | ows sign send-tx \
        --chain eip155:11155111 --wallet $WALLET \
        --rpc-url $RPC --tx $HEX 2>&1)
    echo "✅ $TO → $RESULT"
    sleep 15
}

while true; do
    BALANCE=$(/opt/agentguard/.venv/bin/python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('$RPC'))
print(float(w3.from_wei(w3.eth.get_balance('$FROM'), 'ether')))
")
    echo "💰 Bakiye: $BALANCE ETH"
    ENOUGH=$(/opt/agentguard/.venv/bin/python3 -c "print('yes' if $BALANCE > 0.002 else 'no')")
    if [ "$ENOUGH" = "no" ]; then
        echo "⛽ Bakiye bitti."
        break
    fi

    # Rastgele adres seç
    ADDR=${ADDRESSES[$((RANDOM % ${#ADDRESSES[@]}))]}
    send_tx $ADDR
done
