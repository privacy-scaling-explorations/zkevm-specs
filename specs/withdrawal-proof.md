# Withdrawals proof

The withdrawals proof verifies the merkle patricia trie identified by the root `withdrawalsRoot` contains all the withdrawals.

`Withdrawal` operation is introduced by EIP-4895 to provides a way for validator withdrawals made on the beacon chain to enter into the EVM. `Withdrawal` operation is a system-level operation and introduces a new field after the existing fields in the execution payload. Unlike transactions, there is no signature to verify and the main verification logic is to verify withdrawals MPT root which happens in MPT circuit. Since `withdrawal` is a system-level operation, the balance change is unconditional and won't fail.

## Withdrawal encoding

The execution payload gains a new field for the withdrawals which is an RLP list of Withdrawal data. This new field is encoded after the existing fields in the execution payload structure and is considered part of the execution payload’s body.

```
withdrawal_0 = [withdrawal_index_0, validator_index_0, address_0, amount_0]
withdrawal_1 = [withdrawal_index_1, validator_index_1, address_1, amount_1]
withdrawals = [withdrawal_0, withdrawal_1]

execution_payload_body_rlp = RLP([transactions, [], withdrawals])
```


## Circuit behavior

For every withdrawal defined as the parameters `(withdrawal_index, validator_index, address, amount)` and the circuit verifies the followings:

1. `withdrawalsData: bytes = rlp([withdrawal_index, validator_index, address, amount])`
2. `withdrawalsRoot: word = mpt(withdrawalsData)`
3. `withdrawal_index`, `validator_index` and `amount` are all `uint64` values.
4. `amount_wei = amount * 1e9` and increases validator's balance by `amount_wei`

- The rlp encoding of withdrawal parameters will be done using a custom rlp encoding gadget,  isolated from the rlp encoding used by the MPT circuit.
- The MPT root verification will be done in MPT circuit; the withdrawal circuit do a lookup to the MPT table.

From this information the circuit builds the WithdrawalTable:

Where:

- Address = validator's address
- Amount = a nonzero amount of ether given in Gwei (1e9 wei)
- MPT root = an incremental MPT root

| 0 Withdrawal ID | 1 Validator ID | 2 Address      | 3 Amount      | 4 MPT root     |
| -----------     | -------------  | -------------- | ------------- | -------------- |
| $WithdrawalID   | $ValidatorID   | $value{Lo,Hi}  | $value{Lo,Hi} | $value{Lo,Hi}  |

There are some constraints on the shape of the table like:

- `WithdrawalID` is increased monotonically and sequentially for each withdrawal. Which means it won't be starting from 0 in most of cases.
- MPT root is used to lookup MPT table.

Except MPT root, the withdrawal table is built by public input circuit, the public input circuit would validate all rows of the table are properly built. MPT root is part of witness and the value is verified by MPT circuit. Since the table construction is validated outside of the circuit, there's no need to verify the same constraints inside of the circuit. 

### Withdrawal Trie

For each withdrawal, the withdrawal circuit also must prepare the key and value used to build the withdrawal trie.  These keys and values are used in lookups to the MPT table in order to verify that a tree built with the key-values corresponding to the withdrawals has the root value `withdrawalsRoot`.

> By doing lookups to the MPT table, we prove that when we start with an empty MPT, and do a chain of key-value insertions corresponding to each transaction, we reach a Trie with root value `withdrawalsRoot`.

Each MPT update uses the following parameters:

- Key = `rlp(withdrawal_index)`
- Value = `rlp([withdrawal_index, validator_index, address, amount])`
- ValuePrev = `0`

NOTE: The MPT proof used for the Withdrawal Trie doesn't need deletion support.

`go-ethereum` reference:

- [Withdrawal operation separated from user-level transactions ](https://github.com/ethereum/go-ethereum/blob/b8adb4cb0c4989d138506531ef1966793b658c54/core/state_processor.go#L97-L102)
- [Withdrawal logic: increasing balance only](https://github.com/ethereum/go-ethereum/blob/b8adb4cb0c4989d138506531ef1966793b658c54/consensus/beacon/consensus.go#L356-L357)
- [Withdrawal RLP encoding](https://github.com/ethereum/go-ethereum/blob/b8adb4cb0c4989d138506531ef1966793b658c54/core/types/withdrawal.go#L54-L57)

## Code

Please refer to `src/zkevm-specs/withdrawal_circuit.py`.
