# ZKEVM Introduction

At the moment every node on Ethereum has to validate every transaction in the Ethereum virtual machine. This means that every transaction adds work that everyone needs to do to verify Ethereum's history. Worse still is that each transaction needs to be verified by every new node. Which means the amount of work a new node needs to do the sync the network is growing constantly. We want to build a proof of validity for the Ethereum blocks to avoid this. There are two goals.

1. Make a zkrollup that supports smart contracts
2. Create a proof of validity for every Ethereum block

This means making a proof of validity for the EVM + state reads  / writes + signatures.

To simplify we separate our proofs into two components.

1. **State proof**: State/memory/stack ops have been performed correctly. This does not check if the correct location has been read/written. We allow our prover to pick any location here and in the EVM proof confirm it is correct.
2. **EVM proof**: This checks that the correct opcode is called at the correct time. It checks the validity of these opcodes. It also confirms that each of these opcodes and the state proof performed the correct operation.

Only after verifying both proofs are valid, we have confidence that Ethereum block is executed correctly.
