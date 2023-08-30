# State Proof

The state proof helps EVM proof to check all the random read-write access records are valid, through grouping them by their unique index first, and then sorting them by order of access. We call the order of access `ReadWriteCounter`, which counts the number of access records and also serves as an unique identifier for a record. When state proof is generated, the `BusMapping` is also produced and will be shared to EVM proof as a lookup table.

## Random Read-Write Data

State proof maintains the read-write part of [random accessible data](./evm-proof.md#Random-Accessible-Data) of EVM proof.

The operations recorded in the state proof are:

1. `Start`: Start of transaction and padding row
2. `Memory`: Call's memory as a byte array
3. `Stack`: Call's stack as RLC-encoded word array
4. `Storage`: Account's storage as key-value mapping
5. `CallContext`: Context of a Call
6. `Account`: Account's state (nonce, balance, code hash)
7. `TxRefund`: Value to refund to the tx sender
8. `TxAccessListAccount`: State of the account access list
9. `TxAccessListAccountStorage`: State of the account storage access list
10. `TxLog`: State of the transaction log
11. `TxReceipt`: State of the transaction receipt

Each operation uses different parameters for indexing.  See [RW Table](./tables.md#rw_table) for the complete details.

The concatenation of all table keys becomes the unique index for data. Each record will be attached with a `ReadWriteCounter`, and the records are constraint to be in group by their unique index first and to be sorted by their `ReadWriteCounter` increasingly. Given the access to previous record, each target has their own format and rules to update, for example, values in `Memory` should fit in 8-bit.

## Circuit Constraints

The constraints are divided into two groups:

- Global constraints that affect all operations, like the lexicographic order of keys.
- Particular constraints to each operation.  A selector-like expression is used for every operation type to enable extra constraints that only apply to that operation.

For all the constraints that must guarantee proper ordering/transition of
values we use range checks of the difference between the consecutive cells,
with the help of fixed lookup tables.  Since we use lookup tables to prove
correct ordering, for every column that must be sorted we need to define the
maximum value it can contain (which will correspond to the fixed lookup table
size); this way, two consecutive cells in order will have a difference that is
found in the table, and a reverse ordering will make the difference to wrap
around to a very high value (due to the field arithmetic), causing the result
to not be in the table.

### Start
- 1.0. `field_tag`, `address` and `id`, `storage_key` are 0
- 1.1. `rw counter` increases if it's not first row
- 1.2. `value` is 0
- 1.3. `initial_value` is 0
- 1.4. `state root` is the same if it's not first row

### Memory
- 2.0. `field_tag` and `storage_key` are 0
- 2.1. `value` is 0 if first access and `READ`
- 2.2. Memory address is in 32 bits range
- 2.3. `value` is byte
- 2.4. `initial_value` is 0
- 2.5. `state root` is the same

### Stack

- 3.0. `field_tag` and `storage_key` are 0
- 3.1. First access is WRITE
- 3.2. Stack pointer is less than 1024
- 3.3. Stack pointer increases 0 or 1 only
- 3.4. `initial_value` is 0
- 3.5. `state root` is the same

### Storage
- 4.0. `field_tag` is 0
- 4.1. MPT lookup for last access to (address, storage_key)

### Call Context
- 5.0. `address` and `storage_key` are 0
- 5.1. `field_tag` is in CallContextFieldTag range
- 5.2. `value` is 0 if first access and READ
- 5.3. `initial value` is 0
- 5.4. `state root` is the same

### Account
- 6.0. `id` and `storage_key` are 0
- 6.1. MPT storage lookup for last access to (address, field_tag)

### Tx Refund
- 7.0. `address`, `field_tag` and `storage_key` are 0
- 7.1. `state root` is the same
- 7.2. `initial_value` is 0
- 7.3. First access for a set of all keys are 0 if `READ`

### Tx Access List Account
- 8.0. `field_tag` and `storage_key` are 0
- 8.1. `state root` is the same
- 8.2. First access for a set of all keys are 0 if `READ`


### Tx Access List Account Storage
- 9.0. `field_tag` is 0
- 9.1. `state root` is the same
- 9.2. First access for a set of all keys are 0 if `READ`

### Tx Log
- 10.0. `is_write` is 1
- 10.1. `state root` is the same

### Tx Receipt
- 11.0. `address` and `storage_key` are 0
- 11.1. `field_tag` is boolean (according to EIP-658)
- 11.2. `tx_id` increases by 1 and `value` increases as well if `tx_id` changes 
- 11.3. `tx_id` is 1 if it's the first row and `tx_id` is in 11 bits range
- 11.4. `state root` is the same

## About Account and Storage accesses

All account and storage reads and writes in the RwTable are linked to the Merkle
Patricia Trie (MPT) Circuit.  This is because unlike the rest of entries, which
are initialized at 0 in each block, account and storage persist during blocks via
the Ethereum State and Storage Tries.

In general we link the first and last accesses of each key (`[address,
field_tag]` for Account, `[address, storage_key]` for Storage) to MPT proofs that
use chained roots (the `root_next` of a proof matches the `root_previous` of the
next proof).  Finally we match the `root_previous` of the first proof with the
`block_previous.root` and the `root_next` of the last proof with the
`block_next.root`.

Linking the account and storage accesses with MPT proofs requires treating
existing/non-existing cases separately: the EVM supports reading Account
fields for non-existing accounts and Storage slots for non-existing slots; but
since those values don't exists, a MPT inclusion proof can't be verified.
Moreover, some EVM situations require explicitly verifying that an account
doesn't exist.  On the MPT side this is solved by introducing non-existing
proofs.  The rules to link read/write access to accounts (as done by the EVM
Circuit to the RwTable) and the MPT existence/non-existence proof are described
[here](/specs/evm-proof.md#account-non-existence)

## Code

Please refer to `src/zkevm-specs/state_circuit.py`
