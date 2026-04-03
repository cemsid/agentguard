#!/bin/bash

WALLET="my-agent"
PASSWORD=""
RPC="https://ethereum-sepolia-rpc.publicnode.com"
FROM="0x398F62F487a9138398B5fdE08e07beBA8698E804"
TO="0x000000000000000000000000000000000000dEaD"

send_tx() {
    local VALUE=$1
    HEX=$(/opt/agentguard/.venv/bin/python3 << PYEOF
from web3 import Web3
import rlp
w3 = Web3(Web3.HTTPProvider("$RPC"))
nonce    = w3.eth.get_transaction_count("$FROM", "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
tip      = w3.to_wei(2, "gwei")
max_fee  = base_fee + tip
payload  = rlp.encode([11155111, nonce, tip, max_fee, 21000,
    bytes.fromhex("$TO"[2:]), w3.to_wei($VALUE, "ether"), b"", []])
print("02" + payload.hex())
PYEOF
)
    RESULT=$(echo "$PASSWORD" | ows sign send-tx \
        --chain eip155:11155111 --wallet $WALLET \
        --rpc-url $RPC --tx $HEX 2>&1)
    echo "$RESULT"
    sleep 15
}

echo "=== Bakiye bitene kadar tx gönderiliyor ==="

# Sürekli döngü — bakiye 0.002 ETH altına düşünce dur
while true; do
    # Bakiye kontrol
    BALANCE=$(/opt/agentguard/.venv/bin/python3 << PYEOF
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("$RPC"))
bal = w3.eth.get_balance("$FROM")
print(float(w3.from_wei(bal, "ether")))
PYEOF
)
    echo "💰 Bakiye: $BALANCE ETH"

    # 0.002 ETH'den azsa dur
    ENOUGH=$(/opt/agentguard/.venv/bin/python3 -c "print('yes' if $BALANCE > 0.002 else 'no')")
    if [ "$ENOUGH" = "no" ]; then
        echo "⛽ Bakiye bitti, duruyorum."
        break
    fi

    # Rastgele success veya failed tx gönder
    RAND=$((RANDOM % 5))
    if [ $RAND -le 3 ]; then
        echo "✅ Normal tx gönderiliyor..."
        send_tx 0.0001
    else
        echo "💥 Büyük tx (fail olacak)..."
        send_tx 50  # bakiyeden fazla — fail olur
    fi
done

echo "✅ Tamamlandı!"
