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
- **value, intialValue**: variable size, depending on Tag (key0) and FieldTag (key3) where appropriate.
- **root**: RLC encoded MPT state root.
- **(rw) counter**: 32 bits, starts at 1.
- **txID**: 32 bits, starts at 1 (corresponds to `txIndex + 1`).
- **address**: 160 bits
- **callID**: 32 bits, starts at 1 (corresponds to `rw_counter` when the call begins).
- **Stack -> stackPointer**: 10 bits
- **Memory -> memoryAddress**: 32 bits
- **Memory -> value**: 1 byte
- **storageKey**: field size, RLC encoded (Random Linear Combination).
- **TxLog Address column**:  Packs 2 values:
    - **TxLog -> logID**: 32 bits, starts at 1 (corresponds to `logIndex + 1`), it is unique per tx/receipt.
    - **TxReceipt -> topicIndex, byteIndex**: 32 bits, indicates order in tx log topics or data.
- **TxLog -> Topic -> value**: field size, RLC encoded (Random Linear Combination).
- **TxLog -> Data -> value**: 1 byte
- **TxReceipt -> PostStateOrStatus**: 1 byte
- **TxReceipt -> CumulativeGasUsed**: 64 bits

NOTE: `kN` means `keyN`

| 0 *Rwc*  | 1 *IsWrite* | 2 *Tag* (k0)               | 3 *Id* (k1) | 4 *Address* (k2)   | 5 *FieldTag* (k3)          | 6 *StorageKey* (k4) | 7 *Value* | 8 *InitialValue* | 9 *Root* |
| -------- | ----------- | -------------------------- | --------    | --------           | -------------------------- | -----------         | --------- | ---------------- | --------  |
|          |             | *RwTableTag*               |             |                    |                            |                     |           |                  |              |
| $counter | true        | TxAccessListAccount        | $txID       | $address           |                            |                     | $value    | 0                | $root |
| $counter | true        | TxAccessListAccountStorage | $txID       | $address           |                            | $storageKey         | $value    | 0                | $root |
| $counter | $isWrite    | TxRefund                   | $txID       |                    |                            |                     | $value    | 0                | $root |
|          |             |                            |             |                    |                            |                     |           |                  |         |
|          |             |                            |             |                    | *AccountFieldTag*          |                     |           |                  | |
| $counter | $isWrite    | Account                    |             | $address           | Nonce                      |                     | $value    | $committedValue  | $root |
| $counter | $isWrite    | Account                    |             | $address           | Balance                    |                     | $value    | $committedValue  | $root |
| $counter | $isWrite    | Account                    |             | $address           | CodeHash                   |                     | $value    | $committedValue  | $root |
| $counter | $isWrite    | Account                    |             | $address           | NonExisting                |                     | 0         | 0                | $root |
| $counter | true        | AccountDestructed          |             | $address           |                            |                     | $value    | 0                | $root |
|          |             |                            |             |                    |                            |                     |           |                  |                 |
|          |             | *CallContext constant*     |             |                    | *CallContextFieldTag* (ro) |                     |           |                  |                 |
| $counter | false       | CallContext                | $callID     |                    | RwCounterEndOfReversion    |                     | $value    | 0                | $root               |
| $counter | false       | CallContext                | $callID     |                    | CallerId                   |                     | $value    | 0                | $root              |
| $counter | false       | CallContext                | $callID     |                    | TxId                       |                     | $value    | 0                | $root              |
| $counter | false       | CallContext                | $callID     |                    | Depth                      |                     | $value    | 0                | $root              |
| $counter | false       | CallContext                | $callID     |                    | CallerAddress              |                     | $value    | 0                | $root              |
| $counter | false       | CallContext                | $callID     |                    | CalleeAddress              |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | CallDataOffset             |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | CallDataLength             |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | ReturnDataOffset           |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | ReturnDataLength           |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | Value                      |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | IsSuccess                  |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | IsPersistent               |                     | $value    | 0               | $root              |
| $counter | false       | CallContext                | $callID     |                    | IsStatic                   |                     | $value    | 0               | $root              |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             | *CallContext last callee*  |             |                    | *CallContextFieldTag* (rw) |                     |            |            |                 |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeId               |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeReturnDataOffset |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeReturnDataLength |                     | $value     | 0               | $root              |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             | *CallContext state*        |             |                    | *CallContextFieldTag* (rw) |                     |            |            |                 |
| $counter | $isWrite    | CallContext                | $callID     |                    | IsRoot                     |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | IsCreate                   |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | CodeHash                   |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | ProgramCounter             |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | StackPointer               |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | GasLeft                    |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | MemorySize                 |                     | $value     | 0               | $root              |
| $counter | $isWrite    | CallContext                | $callID     |                    | ReversibleWriteCounter     |                     | $value     | 0               | $root              |
|          |             |                            |             |                    |                            |                     |            |            |                 |
| $counter | $isWrite    | Stack                      | $callID     | $stackPointer      |                            |                     | $value     | 0               | $root              |
| $counter | $isWrite    | Memory                     | $callID     | $memoryAddress     |                            |                     | $value     | 0               | $root              |
| $counter | $isWrite    | AccountStorage             | $txID       | $address           |                            | $storageKey         | $value     | $committedValue |
|          |             |                            |             |                    |                            |                     |            |            |                 |
|          |             |                            |             |                    | *TxLogTag*                 |                     |            |            |                 |
| $counter | true        | TxLog                      | $txID       | $logID,0           | Address                    | 0                   | $value     | 0               | $root              |
| $counter | true        | TxLog                      | $txID       | $logID,$topicIndex | Topic                      | 0                   | $value     | 0               | $root              |
| $counter | true        | TxLog                      | $txID       | $logID,$byteIndex  | Data                       | 0                   | $value     | 0               | $root              |
| $counter | true        | TxLog                      | $txID       | $logID,0           | TopicLength                | 0                   | $value     | 0               | $root |
| $counter | true        | TxLog                      | $txID       | $logID,0           | DataLength                 | 0                   | $value     | 0               | $root |
|          |             |                            |             |                    |                            |                     |            |            |       |
|          |             |                            |             |                    | *TxReceiptTag*             |                     |            |            |  |
| $counter | false       | TxReceipt                  | $txID       | 0                  | PostStateOrStatus          | 0                   | $value     | 0               | $root |
| $counter | false       | TxReceipt                  | $txID       | 0                  | CumulativeGasUsed          | 0                   | $value     | 0               | $root |
| $counter | false       | TxReceipt                  | $txID       | 0                  | LogLength                  | 0                   | $value     | 0               | $root |

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
- Key
- ValuePrev
- Value
- RootPrev
- Root

The circuit can prove that updates to account nonces, balances, or storage slots are correct, or that an account's code hash is some particular value. Note that it is not possible to change the code hash for an account without deleting it and then recreating it.

| Address | ProofType               | Key  | ValuePrev     | Value        | RootPrev  | Root  |
| ------- | ----------------------- | ---- | ------------- | ------------ | --------- | ----- |
| $addr   | NonceMod                | 0    | $noncePrev    | $nonceCur    | $rootPrev | $root |
| $addr   | BalanceMod              | 0    | $balancePrev  | $balanceCur  | $rootPrev | $root |
| $addr   | CodeHashMod             | 0    | $codeHashPrev | $codeHashCur | $rootPrev | $root |
| $addr   | NonExistingAccountProof | 0    | 0             | 0            | $root     | $root |
| $addr   | AccountDeleteMod        | 0    | 0             | 0            | $rootPrev | $root |
| $addr   | StorageMod              | $key | $valuePrev    | $value       | $rootPrev | $root |
| $addr   | NonExistingStorageProof | $key | 0             | 0            | $root     | $root |

## `Keccak Table`

See [tx.py](src/zkevm_specs/tx.py)

| IsEnabled | InputRLC   | InputLen | Output      |
| --------- | ---------- | -------- | ----------- |
| bool      | $input_rlc | $input_length | $output_rlc |

Column names in circuit:
- IsEnabled: `is_final`
- InputRLC: `data_rlc`
- InputLen: `length`
- Output: `hash_rlc`


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

## Exponentiation Table

Proved by the Exponentiation circuit.

The exponentiation table is a virtual table within the exponentiation circuit assignments. An exponentiation operation `a ^ b == c (mod 2^256)` is broken down into steps that perform the exponentiation by squaring.

The following algorithm is used for exponentiation by squaring:
```
Function exp_by_squaring(x, n)
    if n = 0  then return  1;
    if n = 1  then return  x;
    if n is odd:
	return x * exp_by_squaring(x, n - 1)
    if n is even:
	return (exp_by_squaring(x, n / 2))^2
```

Using the above algorithm, `3 ^ 13 == 1594323 (mod 2^256)` is broken down into the following steps:
```
3      * 3   = 9
9      * 3   = 27
27     * 27  = 729
729    * 729 = 531441
531441 * 3   = 1594323
```

We assign the above steps to the exponentiation table in the reverse order, so that the first step is `531441 * 3 = 1594323`. From here on, the RHS in the above steps is termed as `intermediate_exponentiation`. We define another term `intermediate_exponent` as a value that starts at the integer exponent of the operation, i.e. `13` in the above case, and reduces down to `2` such that:
```
if intermediate_exponent::cur is even:
	intermediate_exponent::next = intermediate_exponent::cur // 2
else:
	intermediate_exponent::next == intermediate_exponent::cur - 1
```

The exponentiation table consist of 4 columns, namely:
1. `identifier`: An identifier (currently read-write counter at which the exponentiation table is looked up) to uniquely identify an exponentiation trace.
2. `is_last`: A boolean value to indicate the last row of the exponentiation trace's table assignments.
3. `base_limb`: 64-bit limb representing the integer base of the exponentiation operation.
4. `exponent_lo_hi`: 128-bit low/high parts of an intermediate value that starts at the integer exponent.
5. `exponentiation_lo_hi`: 128-bit low/high parts of an intermediate value that starts at the result of the exponentation operation.

The lookup entry is not a single row in the table, and not every row corresponds to a lookup entry. Instead, a lookup entry is constructed from the first 4 rows in each exponentiation event. For simplicity in the `specs` implementation, we combine all those rows into a single row. But in the `circuits` implementation, we try to lower the number of columns in exchange of increased number of rows.

Depending on the value of the `exponent` within the exponentiation operation, the `EXP` gadget will either:
1. Do no lookup if `exponent == 0` since `base ^ 0 == 1 (mod 2^256)`
2. Do no lookup if `exponent == 1` since `base ^ 1 == base (mod 2^256)`
3. Do 1 lookup to a row if `exponent == 2` since there is a single step in the exponentiation trace, i.e. `base ^ 2 == base * base (mod 2^256)`, implying that `is_first == is_last == 1` for this row.
4. Do 2 lookups to 2 different rows if `exponent > 2` since there are more than one steps in the exponentiation trace, i.e. a lookup to `is_last == 0` and a lookup to `is_last == 1`.

Consider `3 ^ 13 == 1594323 (mod 2^256)`. The exponentiation table assignment looks as follows:

| identifier | is_last | base_limb0 | base_limb1 | base_limb2 | base_limb3 | exponent_lo | exponent_hi | lsb_exponent | exponentiation_lo | exponentiation_hi |
|------------|---------|------------|------------|------------|------------|-------------|-------------|--------------|-------------------|-------------------|
| $rwc       | 0       | 3          | 0          | 0          | 0          | 13          | 0           | 13           | 1594323           | 0                 |
| $rwc       | 0       | 3          | 0          | 0          | 0          | 12          | 0           | 12           | 531441            | 0                 |
| $rwc       | 0       | 3          | 0          | 0          | 0          | 6           | 0           | 6            | 729               | 0                 |
| $rwc       | 0       | 3          | 0          | 0          | 0          | 3           | 0           | 3            | 27                | 0                 |
| $rwc       | 1       | 3          | 0          | 0          | 0          | 2           | 0           | 2            | 9                 | 0                 |

For `exponent == 13`, i.e. scenario #4 we do two lookups:
1. Lookup to first row:
```
Row(identifier=rwc, is_last=0, base_limbs=[3, 0, 0, 0], exponent_lo_hi=[13, 0], lsb_exponent=13, exponentiation_lo_hi=[1594323, 0])
```
2. Lookup to last row:
```
Row(identifier=rwc, is_last=1, base_limbs=[3, 0, 0, 0], exponent_lo_hi=[2, 0], lsb_exponent=2, exponentiation_lo_hi=[9, 0])
```
