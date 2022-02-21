# State Proof

The state proof helps EVM proof to check all the random read-write access records are valid, through grouping them by their unique index first, and then sorting them by order of access. We call the order of access `ReadWriteCounter`, which counts the number of access records and also serves as an unique identifier for a record. When state proof is generated, the `BusMapping` is also produced and will be shared to EVM proof as a lookup table.

## Random Read-Write Data

State proof maintains the read-write part of [random accessible data](./evm-proof.md#Random-Accessible-Data) of EVM proof.

The operations recorded in the state proof are:

- `Memory`: Call's memory as a byte array
- `Stack`: Call's stack as RLC-encoded word array
- `Storage`: Account's storage as key-value mapping
- `CallContext`: Context of a Call
- `Account`: Account's state (nonce, balance, code hash)
- `TxRefund`: Value to refund to the tx sender
- `TxAccessListAccount`: State of the account access list
- `TxAccessListAccountStorage`: State of the account storage access list
- `AccountDestructed`: State of destruction of an account

Each operation uses diferent parameters for indexing.  See [RW Table](./tables.md#rw_table) for the complete details.

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

The exact list of constraints is documented in detail as comments in the python
code implementation.

## Code

Please refer to `src/zkevm-specs/state.py`
