# Invalid transaction proof

## Type of invalid transaction
According to [Taiko whitepaper](https://github.com/taikochain/whitepaper), we still generate proof for invalid transactions. A TX is invalid means it dis-obeys the follow rules come from ethereum yellow paper. 

```
6. Transaction Execution
The execution of a transaction is the most complex part of the Ethereum protocol: it defines the state transition function Υ. It is assumed that any transactions executed first pass the initial tests of intrinsic validity. These include:
(1) The transaction is well-formed RLP, with no additional trailing bytes;
(2) the transaction signature is valid;
(3) the transaction nonce is valid (equivalent to the sender account’s current nonce);
(4) the sender account has no contract code deployed (see EIP-3607 by Feist et al. [2021]);
(5) the gas limit is no smaller than the intrinsic gas, g0, used by the transaction; and
(6) the sender account balance contains at least the cost, v0, required in up-front payment.
```

However we don't check all of them in evm_circuit. Some checks can be done in the contract. So we separate TX to these 3 types:
1. `Good TX`: A TX can be executed successfully, which means it comply with that 6 rules defined by the eth yellow paper.
2. `Neutral bad TX`: A bad TX, but the failure is becuase sth out of a miner's control, e.g., a nonce conflicting TX.
3. `Malicious bad TX`: A bad TX, but it is submitted because of a malicious proposer. For example: a TX with wrong signature, normal miner filter it out. The txList contains TX in this type is also treated as invalid txList.
We use a conditional filter flag `neutral_bad_tx` to tell the difference between type 2 & 3, if the flag is set, the type 2 TX is still handled by the circuit, without any change to state DB. 

## Proof of invalid transaction

Below is the list of invalid transaction types and their handler methods. `!` means contrary as usual.
(1). `!`the transaction is well-formed RLP, with no additional trailing bytes
Category: Type 3.
Solution: RLP decoding is verified by a RLP circuit, wrong RLP leads to wrong/non-existent proof, and a honest miner could easily tell the contract the RLP is problematic.

(2). `!`The transaction signature is valid;
Category: Type 3.
Solution: The signature is checked by evm circuit without conditional filter. So if a TX has invalid signature, no valid proof can be generated, and the whole txList is marked as invalid because only malicious miner packs invalid signature. Meanwhile we depend on one honest miner to submit a InvalidTxListProof and expose that invalid sig TX to the smart contract.

(3) `!`the transaction nonce is valid (equivalent to the sender account’s current nonce);
Category: Type 2.
Solution: Conditional filtering in evm circuit. As `naatral_bad_tx` == true, we just skip this TX while processing the txlist in circuit, see [Circuit Constraints](#circuit-constraints) section.

(4) `!`the sender account has no contract code deployed (see EIP-3607 by Feist et al. [2021]);
Category: Type 3.
Solution: As long as the address conflict is infeasible, we treat this as impossible so far.

(5) `!`the gas limit is no smaller than the intrinsic gas, g0, used by the transaction;
Category: Type 3.
Solution: Pretty like invalid sig processing. No valid proof can be generated if it happens, and a honest miner could easily tell the contract this one is incorrect. The only thing need to care is that the contract needs to handle nil RLP encoding correctly.

(6) `!`the sender account balance contains at least the cost, v0, required in up-front payment.
Category: Type 2.
Solution: Same as (3)

So, We actually make the circuit know all these types, and then, Only 2 `neutral_bad_tx` types have normal circuit proof and the rest does not.

## Circuit Constraints
- For a TX in tx table
  - A binary column called `neutral_bad_tx` in tx_table.
  - If `tx_nonce != nonce_prev` then `neutral_bad_tx == true` else `neutral_bad_tx == false`.
  - If `tx_value > value_prev + gas_price * gas_limit` then `neutral_bad_tx == true` else `neutral_bad_tx == false`.
  - If `neutral_bad_tx == true` then `next_exec_step == end_tx`.
- Any other modules who uses `tx_table`
  - Tx-trie circuit to exclude these `neutral_bad_tx` == true TXs.
  - Public input/Ecdsa/Keccak/etc circuits to ignore `neutral_bad_tx` cell. 

## Code
Please refer to [Begin TX execution](`src/zkevm-specs/exp_circuit.py`).
Almost all circuit modules change more or less because tx_table changes.