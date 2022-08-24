# Tables

For the zkevm we use the following dynamic and fixed tables for lookups to the EVM circuit.  The validity of the dynamic tables contents is proved by their own associated circuit.

Code spec at [table.py](../src/zkevm_specs/evm/table.py)

## `tx_table`

Proved by the tx circuit.

| 0 TxID | 1 Tag               | 2          | 3 value |
| ---    | ---                 | ---        | ---     |
|        | *TxContextFieldTag* |            |         |
| $TxID  | Nonce               | 0          | $value  |
| $TxID  | Gas                 | 0          | $value  |
| $TxID  | GasPrice            | 0          | $value  |
| $TxID  | CallerAddress       | 0          | $value  |
| $TxID  | CalleeAddress       | 0          | $value  |
| $TxID  | IsCreate            | 0          | $value  |
| $TxID  | Value               | 0          | $value  |
| $TxID  | CallDataLength      | 0          | $value  |
| $TxID  | CallDataGasCost     | 0          | $value  |
| $TxID  | TxSignHash          | 0          | $value  |
| $TxID  | CallData            | $ByteIndex | $value  |
| $TxID  | Pad                 | 0          | $value  |

NOTE: `CallDataGasCost` and `TxSignHash` are values calculated by the verifier
and used to reduce the circuit complexity.  They may be removed in the future.

## `rw_table`

Proved by the state circuit.

> - **CallContext constant**: read-only data in a call, usually checked with the
>   caller before the beginning of a call.
> - **CallContext state**: used by caller to save its own CallState when it's going
>   to dive into another call, and will be read out to restore caller's
>   CallState in the end by callee.
> - **CallContext last callee**: read-only data inside a call like previous section
>   for opcode `RETURNDATASIZE` and `RETURNDATACOPY`, except they will be
>   updated when end of callee execution.

Details:

- **Address (key2)** is reserved for stack, memory, and account addresses.
- **StorageKey (key4)** is reserved for RLC encoded values
- **value, valuePrev**: variable size, depending on Tag (key0) and FieldTag (key3) where appropriate.
- **(rw) counter**: 32 bits, starts at 1.
- **txID**: 32 bits, starts at 1 (corresponds to `txIndex + 1`).
- **address**: 160 bits
- **callID**: 32 bits, starts at 1 (corresponds to `rw_counter` when the call begins).
- **Stack -> stackPointer**: 10 bits
- **Memory -> memoryAddress**: 32 bits
- **Memory -> value, valuePrev**: 1 byte
- **storageKey**: field size, RLC encoded (Random Linear Combination).
- **TxLog Address column**:  Packs 2 values:
    - **TxLog -> logID**: 32 bits, starts at 1 (corresponds to `logIndex + 1`), it is unique per tx/receipt.
    - **TxReceipt -> topicIndex, byteIndex**: 32 bits, indicates order in tx log topics or data.
- **TxLog -> Topic -> value**: field size, RLC encoded (Random Linear Combination).
- **TxLog -> Data -> value**: 1 byte
- **TxReceipt -> PostStateOrStatus**: 1 byte
- **TxReceipt -> CumulativeGasUsed**: 64 bits

NOTE: `kN` means `keyN`

| 0 *Rwc*  | 1 *IsWrite* | 2 *Tag* (k0)               | 3 *Id* (k1) | 4 *Address* (k2)   | 5 *FieldTag* (k3)          | 6 *StorageKey* (k4) | 7 *Value0* | 8 *Value1* | 9 *Aux0*        |
| -------- | ----------- | -------------------------- | --------    | --------           | -------------------------- | -----------         | ---------  | ---------- | --------------- |
|          |             | *RwTableTag*               |             |                    |                            |                     |            |            |                 |
| $counter | true        | TxAccessListAccount        | $txID       | $address           |                            |                     | $value     | $valuePrev | 0               |
| $counter | true        | TxAccessListAccountStorage | $txID       | $address           |                            | $storageKey         | $value     | $valuePrev | 0               |
| $counter | $isWrite    | TxRefund                   | $txID       |                    |                            |                     | $value     | $valuePrev | 0               |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             |                            |             |                    | *AccountFieldTag*          |                     |            |            |                 |
| $counter | $isWrite    | Account                    |             | $address           | Nonce                      |                     | $value     | $valuePrev | $committedValue |
| $counter | $isWrite    | Account                    |             | $address           | Balance                    |                     | $value     | $valuePrev | $committedValue |
| $counter | $isWrite    | Account                    |             | $address           | CodeHash                   |                     | $value     | $valuePrev | $committedValue |
| $counter | true        | AccountDestructed          |             | $address           |                            |                     | $value     | $valuePrev | 0               |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             | *CallContext constant*     |             |                    | *CallContextFieldTag* (ro) |                     |            |            |                 |
| $counter | false       | CallContext                | $callID     |                    | RwCounterEndOfReversion    |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | CallerId                   |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | TxId                       |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | Depth                      |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | CallerAddress              |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | CalleeAddress              |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | CallDataOffset             |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | CallDataLength             |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | ReturnDataOffset           |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | ReturnDataLength           |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | Value                      |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | IsSuccess                  |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | IsPersistent               |                     | $value     | 0          | 0               |
| $counter | false       | CallContext                | $callID     |                    | IsStatic                   |                     | $value     | 0          | 0               |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             | *CallContext last callee*  |             |                    | *CallContextFieldTag* (rw) |                     |            |            |                 |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeId               |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeReturnDataOffset |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeReturnDataLength |                     | $value     | 0          | 0               |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             | *CallContext state*        |             |                    | *CallContextFieldTag* (rw) |                     |            |            |                 |
| $counter | $isWrite    | CallContext                | $callID     |                    | IsRoot                     |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | IsCreate                   |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | CodeHash                   |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | ProgramCounter             |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | StackPointer               |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | GasLeft                    |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | MemorySize                 |                     | $value     | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID     |                    | ReversibleWriteCounter     |                     | $value     | 0          | 0               |
|          |             |                            |             |                    |                            |                     |            |            |                 |
| $counter | $isWrite    | Stack                      | $callID     | $stackPointer      |                            |                     | $value     | 0          | 0               |
| $counter | $isWrite    | Memory                     | $callID     | $memoryAddress     |                            |                     | $value     | 0          | 0               |
| $counter | $isWrite    | AccountStorage             | $txID       | $address           |                            | $storageKey         | $value     | $valuePrev | $committedValue |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             |                            |             |                    | *TxLogTag*                 |                     |            |            |                 |
| $counter | true        | TxLog                      | $txID       | $logID,0           | Address                    | 0                   | $value     | 0          | 0               |
| $counter | true        | TxLog                      | $txID       | $logID,$topicIndex | Topic                      | 0                   | $value     | 0          | 0               |
| $counter | true        | TxLog                      | $txID       | $logID,$byteIndex  | Data                       | 0                   | $value     | 0          | 0               |
| $counter | true        | TxLog                      | $txID       | $logID,0           | TopicLength                | 0                   | $value     | 0          | 0               |
| $counter | true        | TxLog                      | $txID       | $logID,0           | DataLength                 | 0                   | $value     | 0          | 0               |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             |                            |             |                    | *TxReceiptTag*             |                     |            |            |                 |
| $counter | false       | TxReceipt                  | $txID       | 0                  | PostStateOrStatus          | 0                   | $value     | 0          | 0               |
| $counter | false       | TxReceipt                  | $txID       | 0                  | CumulativeGasUsed          | 0                   | $value     | 0          | 0               |
| $counter | false       | TxReceipt                  | $txID       | 0                  | LogLength                  | 0                   | $value     | 0          | 0               |

## `bytecode_table`

Proved by the bytecode circuit.

> - **tag**: Tag whether the row represents the bytecode length or a byte in
>   the bytecode.

> - **isCode**: A boolean value to specify if the value is executable opcode or
>   the data portion of PUSH\* operations.

| 0 codeHash | 1 tag              | 2 index | 3 isCode | 4 value |
| ---        | ---                | ---     | ---      | ---     |
|            | *BytecodeFieldTag* |         |          |         |
| $codeHash  | Length             | 0       | 0        | $value  |
| $codeHash  | Byte               | $index  | $isCode  | $value  |
| ...        | ...                | ...     | ...      | ...     |
| $codeHash  | Byte               | $index  | $isCode  | $value  |

In the case of an account without code, it can still have a row in the bytecode circuit to represent the `BytecodeFieldTag::Length` tag, with a `value = 0` and `codeHash = EMPTY_CODE_HASH`.

## `block_table`

Proved by the block circuit.

__Note that a generalisation is done by storing the ChainId field inside the block_table__
__when it should indeed live inside of the chain configuration section (which we don't have).__
__Hence the addition inside of the block_table.__

| 0 Tag                  | 1      | 2 value |
| ---                    | ---    | ---     |
| *BlockContextFieldTag* |        |         |
| Coinbase               | 0      | $value  |
| GasLimit               | 0      | $value  |
| BlockNumber            | 0      | $value  |
| Time                   | 0      | $value  |
| Difficulty             | 0      | $value  |
| BaseFee                | 0      | $value  |
| ChainID                | 0      | $value  |
| BlockHash              | 0..256 | $value  |

## `fixed`

> - **execution_state.responsible_opcode()**: map execution_state (opcode's
>   successful cases, where multiple similar opcodes may be merged into a
>   single execution state, like `LT`, `GT`, `EQ` in `CMP` state) to opcode
>   that can generate that execution state.
> - **invalid_opcodes()**: set of invalid opcodes
> - **state_write_opcodes()**: set of opcodes that write the state.
> - **stack_underflow_pairs**: set of opcodes and stack pointer value that
>   causes underflow during execution.
> - **stack_overflow_pairs**: set of opcodes and stack pointer value that
>   causes overflow during execution.

| 0 Tag             | 1                     | 2                                         | 3             |
| ---               | ---                   | ---                                       | ---           |
| *FixedTableTag*   |                       |                                           |               |
| Range16           | 0..16                 | 0                                         | 0             |
| Range32           | 0..32                 | 0                                         | 0             |
| Range64           | 0..64                 | 0                                         | 0             |
| Range256          | 0..256                | 0                                         | 0             |
| Range512          | 0..512                | 0                                         | 0             |
| Range1024         | 0..1024               | 0                                         | 0             |
| SignByte          | value=0..256          | if (value as i8 \< 0) 0xff else 0         | 0             |
| BitwiseAnd        | lhs=0..256            | rhs=0..256                                | $lhs AND $rhs |
| BitwiseOr         | lhs=0..256            | rhs=0..256                                | $lhs OR $rhs  |
| BitwiseXor        | lhs=0..256            | rhs=0..256                                | $lhs XOR $rhs |
| ResponsibleOpcode | $execution_state      | $responsible_opcode                       | $auxiliary    |

## `mpt_table`

Provided by the MPT (Merkle Patricia Trie) circuit.

The current MPT circuit design exposes one big table where different targets require different lookups as described below.
From this table, the following columns contain values using the RLC encoding:
- Address
- Key
- ValuePrev
- ValueCur

## Keccak Table

See [tx.py](src/zkevm_specs/tx.py)

| IsEnabled | InputRLC   | InputLen | Output      |
| --------- | ---------- | -------- | ----------- |
| bool         | $input_rlc | $input_length | $output_rlc |

Column names in circuit:
- IsEnabled: `is_final`
- InputRLC: `data_rlc`
- InputLen: `length`
- Output: `hash_rlc`

### Nonce update

| Enable | Counter  | Address | ValuePrev  | ValueCur  |
| ------ | -------- | ------- | ---------- | --------- |
| 1      | $counter | $addr   | $noncePrev | $nonceCur |

Column names in circuit:
- Enable: `is_nonce_mod`
- Counter: `counter`
- Address: `address_rlc`
- ValuePrev: `sel1`
- ValueCur: `s_mod_node_hash_rlc`

### Balance update

| Enable | Counter  | Address | ValuePrev    | ValueCur    |
| ------ | -------- | ------- | ------------ | ----------- |
| 1      | $counter | $addr   | $balancePrev | $balanceCur |

Column names in circuit:
- Enable: `is_balance_mod`
- Counter: `counter`
- Address: `address_rlc`
- ValuePrev: `sel2`
- ValueCur: `c_mod_node_hash_rlc`

### CodeHash update

| Enable | Counter  | Address | ValuePrev     | ValueCur     |
| ------ | -------- | ------- | ------------- | ------------ |
| 1      | $counter | $addr   | $codeHashPrev | $codeHashCur |

Column names in circuit:
- Enable: `is_codehash_mod`
- Counter: `counter`
- Address: `address_rlc`
- ValuePrev: `sel2`
- ValueCur: `c_mod_node_hash_rlc`

### Storage update

| Enable | Counter  | Address | Key  | ValuePrev  | ValueCur  |
| ------ | -------- | ------- | ---- | ---------- | --------- |
| 1      | $counter | $addr   | $key | $valuePrev | $valueCur |

Column names in circuit:
- Enable: `is_storage_mod`
- Counter: `counter`
- Address: `address_rlc`
- Key: `key_rlc_mult`
- ValuePrev: `mult_diff`
- ValueCur: `acc_c`

### Unified table proposal

We can compress the 4 tables into one at the expense of adding new columns in the MPT circuit.  We still need to analyze the tradeoff of adding columns to the circuit VS merging all the lookups into one.

A unified MPT table would look like this:

| Target   | Counter  | Address | Key  | ValuePrev     | ValueCur     |
| -------- | -------- | ------- | ---- | ------------- | ------------ |
| Nonce    | $counter | $addr   | 0    | $noncePrev    | $nonceCur    |
| Balance  | $counter | $addr   | 0    | $balancePrev  | $balanceCur  |
| CodeHash | $counter | $addr   | 0    | $codeHashPrev | $codeHashCur |
| Storage  | $counter | $addr   | $key | $valuePrev    | $valueCur    |

Columns expressions in circuit:
- Target: `1 * is_nonce_mod + 2 * is_balance_mod + 4 * is_codehash_mod + 8 * is_storage_mod`
- Counter: `counter`
- Address: `address_rlc`
- Key: `key_rlc_mult`
- ValuePrev: `is_nonce_mod * sel1 + is_balance_mod * sel2 + is_codehash_mod * sel2 + is_storage_mod * mult_diff`
- ValueCur: `is_nonce_mod * s_mod_node_hash_rlc + is_balance_mod * c_mod_node_hash_rlc + is_codehash_mod * c_mod_node_hash_rlc + is_storage_mod * acc_c`

## `copy_table`

Proved by the copy circuit.

The copy table consists of 13 columns, described as follows:

- **q_step**: a fixed column for boolean value to indicate a copy step, always alternating between 1 and 0, where 1 indicates a read op and 0 indicates a write op.
- **is_first**: a boolean value to indicate the first row in a copy event.
- **is_last**: a boolean value to indicate the last row in a copy event.
- **ID**: could be `$txID`, `$callID`, `$codeHash` (RLC encoded).
- **Type**: indicates the type of data source, including `Memory`, `Bytecode`, `TxCalldata`, `TxLog` and `RlcAcc`.
- **Address**: indicates the address in the source data, could be memory address, byte index in the bytecode, tx call data, and tx log data. When the data type is `TxLog`, the address is the combination of byte index, `TxLogFieldTag.Data` tag, and `LogID`.
- **AddressEnd**: indicates the address boundary of the source data. Any data read from address greater than or equal to `AddressEnd` should be 0. Note `AddressEnd` is only valid for read operations or `q_step` is 1.
- **BytesLeft**: indicates the number of bytes left to be copied.
- **Value**: indicates the value read or write from source or to the destination.
- **RlcAcc**: indicates the RLC representation of an accumulator value over all write values.
- **Pad**: indicates if the value read from the source is padded. Only valid for read operations or `q_step` is 1.
- **IsCode**: a boolean value to indicate if the `Value` is an executable opcode or the data portion of `PUSH*` operations. Only valid when `Type` is `Bytecode`.
- **RwCounter**: indicates the current RW counter at this row. This value will be used in the lookup to the `rw_table` when `Type` is  `Memory` or `TxLog`.
- **RwcIncreaseLeft**: indicates how much the RW counter will increase in a copy event.


Unlike other lookup tables, the copy table is a virtual table. The lookup entry is not a single row in the table, and not every row corresponds to a lookup entry.
Instead, a lookup entry is constructed from the first two rows in each copy event as
`(is_first, ID, Type, ID[1], Type[1], Address, AddressEnd, Address[1], BytesLeft, RlcAcc, RwCounter, RwcIncreaseLeft)`, where `is_first` is 1 and `Column[1]` indicates the next row in the corresponding column.

The table below lists all of copy pairs supported in the copy table:
- Copy from Tx call data to memory (`CALLDATACOPY`).
- Copy from caller/callee memory to callee/caller memory (`CALLDATACOPY`, `RETURN` (not create), `RETURNDATACOPY`, `REVERT`).
- Copy from bytecode to memory (`CODECOPY`, `EXTCODECOPY`).
- Copy from memory to bytecode (`CREATE`, `CREATE2`, `RETURN` (create))
- Copy from memory to TxLog in the `rw_table` (`LOGX`)
- Copy from memory to RlcAcc (`SHA3`)

| q_step | q_first | q_last | ID        | Type       | Address        | AddressEnd     | BytesLeft  | Value  | RlcAcc  | IsCode  | Pad | RwCounter | RwcIncreaseLeft |
|--------|---------|--------|-----------|------------|----------------|----------------|------------|--------|---------|---------|-----|-----------|-----------------|
| 1      | 0/1     | 0      | $txID     | TxCalldata | $byteIndex     | $cdLength      | $bytesLeft | $value | $rlcAcc | -       | 0/1 | -         | $rwcIncLeft     |
| 0      | 0       | 0/1    | $callID   | Memory     | $memoryAddress | -              | -          | $value | $rlcAcc | -       | 0   | $counter  | $rwcIncLeft     |
|        |         |        |           |            |                |                |            |        | $rlcAcc |         |     |           |                 |
| 1      | 0/1     | 0      | $callID   | Memory     | $memoryAddress | $memoryAddress | $bytesLeft | $value | $rlcAcc | -       | 0/1 | $counter  | $rwcIncLeft     |
| 0      | 0       | 0/1    | $callID   | Memory     | $memoryAddress | -              | -          | $value | $rlcAcc | -       | 0   | $counter  | $rwcIncLeft     |
|        |         |        |           |            |                |                |            |        | $rlcAcc |         |     |           |                 |
| 1      | 0/1     | 0      | $callID   | Memory     | $memoryAddress | $memoryAddress | $bytesLeft | $value | $rlcAcc | $isCode | 0/1 | $counter  | $rwcIncLeft     |
| 0      | 0       | 0/1    | $codeHash | Bytecode   | $byteIndex     | -              | -          | $value | $rlcAcc | $isCode | 0   | -         | $rwcIncLeft     |
|        |         |        |           |            |                |                |            |        | $rlcAcc |         |     |           |                 |
| 1      | 0/1     | 0      | $codeHash | Bytecode   | $byteIndex     | $codeLength    | $bytesLeft | $value | $rlcAcc | $isCode | 0/1 | -         | $rwcIncLeft     |
| 0      | 0       | 0/1    | $callID   | Memory     | $memoryAddress | -              | -          | $value | $rlcAcc | $isCode | 0   | $counter  | $rwcIncLeft     |
|        |         |        |           |            |                |                |            |        | $rlcAcc |         |     |           |                 |
| 1      | 0/1     | 0      | $callID   | Memory     | $memoryAddress | $memoryAddress | $bytesLeft | $value | $rlcAcc | -       | 0/1 | $counter  | $rwcIncLeft     |
| 0      | 0       | 0/1    | $txID     | TxLog      | $byteIndex \|\| TxLogData \|\| $logID | - | - | $value | $rlcAcc | -       | 0   | $counter  | $rwcIncLeft     |
