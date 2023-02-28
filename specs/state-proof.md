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

1.0. `field_tag`, `address` and `id`, `storage_key` are 0
1.1. `rw counter` is increased if it's not first row
1.2. `value` is 0
1.3. `initial value` is 0
1.4. `state root` is not changed if it's not first row

### Memory

2.0. `field_tag` and `storage_key` are 0
2.1. `value` is 0 if first access and READ
2.2. Memory address is in 32 bits range
2.3. `value` is byte
2.4. `initial value` is 0
2.5. `state root` is not changed

### Stack

3.0. `field_tag` and `storage_key` are 0
3.1. First access is WRITE
3.2. Stack address is in 10 bits range
3.3. Stack address is increated only 0 or 1
3.4. `initial value` is 0
3.5. `state root` is not changed

### Storage

4.0. `storage_key` is 0
4.1. mpt_update exists in mpt circuit for AccountStorage last access

### Tx Refund

7.0. `address`, `field_tag` and `storage_key` are 0
7.1. `state root` is not changed
7.2. `initial value` is 0
7.3. First access for a set of all keys are 0 if READ

## Code

Please refer to `src/zkevm-specs/state_circuit.py`
