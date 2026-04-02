# AgentGuard 60-Second Loom Script

Today I'm showing AgentGuard, a trust layer for AI wallet delegation built on Open Wallet Standard.

First, here is the master treasury wallet. With OWS, one wallet can manage both EVM and Solana addresses.

Next, the owner creates a scoped sub-agent key called SolanaTrader. That key is attached to a policy restricting allowed chains and expiry time.

Now the sub-agent requests a transaction. Before anything is signed, AgentGuard asks for explicit human approval. If I reject it, no signature is produced.

Every outcome is written into the audit log. Then the dashboard recalculates a trust score based on successful, rejected, and failed actions.

Here on the dashboard you can see the trust score, the delegation graph, and the audit log table.

The core idea is simple: OWS gives us programmable wallet delegation, and AgentGuard adds human oversight, visibility, and trust.
