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
| $TxID  | TxInvalid           | 0          | $value  |
| $TxID  | AccessListGasCost   | 0          | $value  |
| $TxID  | CallData            | $ByteIndex | $value  |
| $TxID  | Pad                 | 0          | $value  |

NOTE:
- `CallDataGasCost` and `TxSignHash` are values calculated by the verifier and used to reduce the circuit complexity.  They may be removed in the future.
- `TxInvalid` is a flag to tell the circuit which tx is invalid and should not be executed. We check `balance`, `nonce`, and `intrinsic gas` within `begin_tx`, `end_tx`, and `end_block` steps to make sure all txs being processed are valid, and all others are invalid and not executed. Invalid transactions go from the `begin_tx` state directly to the `end_tx` state and do not have any side effects.
- `AccessListGasCost` is the `accessList` gas cost of the tx, which equals to `sum([G_accesslistaddress + G_accessliststorage * len(TA[j]) for j in len(TA)])` (EIP 2930).

## `rw_table`

There are 10 columns in `rw_table`.
 - col. 0 (*Rwc*) is the read-write counter. 32 bits, starts at 1.
 - col. 1 (*IsWrite*) specify this row is for `read` or `write`.
 - col. 2 (*Tag*) is a tag for different contexts. The content for different *Tag*s are in col. 3 ~ col. 10.
 - col. 3 ~ 10 are the content for different *`Tag`* specified in col. 2 accordingly.
    - col. 3 *Id*
        - **txID**: 32 bits, starts at 1 (corresponds to `txIndex + 1`).
        - **callID**: 32 bits, starts at 1 (corresponds to `rw_counter` when the call begins).
    - col. 4 *Address* is the position to **Stack**, **Memory**, or account, where the read or write takes place, depending on the cell value of the *Tag* column.
        - If the *Tag* value is "Account", the cell represents 160 bits **address**.
        - If the *Tag* value is "Stack", the cell represents 10 bits  **stackPointer**.
        - If the *Tag* value is "Memory", the cell represents 32 bits **memoryAddress**.
        - If the *Tag* value is "TxLog", then the cell represents the packing of 2 values:
            - **logID**: 32 bits, starts at 1 (corresponds to `logIndex + 1`), unique per tx/receipt.
            - **topicIndex, byteIndex**: 32 bits, indicates order in tx log topics or data.
    - col. 5 *FieldTag*
        - For *Tag* **TxReceipt**:
            - **PostStateOrStatus**: 8 bits
            - **CumulativeGasUsed**: 64 bits
    - col. 6 *StorageKey* is field size and reserved for RLC encoded (Random Linear Combination) values
    - col. 7 *value* and col. 8 *initialValue*: variable size, depending on Tag (key0) and FieldTag (key3) where appropriate.
        - (*value*) For *Tag* **Memory**: 8 bits
        - (*value*) For *Tag* **TxLog**: 8 bits
            - For *FieldTag* **Topic**: field size, RLC encoded (Random Linear Combination).
            - For *FieldTag* **Data**: 8 bits
    - col. 9 *root*: RLC encoded MPT state root.

The correctness of the rw_table is validated in the state circuit.
> - **CallContext constant**: read-only data in a call, usually checked with the
>   caller before the beginning of a call.
> - **CallContext state**: used by caller to save its own CallState when it's going
>   to dive into another call, and will be read out to restore caller's
>   CallState in the end by callee.
> - **CallContext last callee**: read-only data inside a call like previous section
>   for opcode `RETURNDATASIZE` and `RETURNDATACOPY`, except they will be
>   updated when end of callee execution.


NOTE: `kN` means `keyN`

| 0 *Rwc*  | 1 *IsWrite* | 2 *Tag* (k0)               | 3 *Id* (k1) | 4 *Address* (k2)   | 5 *FieldTag* (k3)          | 6 *StorageKey* (k4) | 7 *Value* | 8 *ValuePrev*    | 9 *Aux1*  | 10 *Aux2* |
| -------- | ----------- | -------------------------- | --------    | --------           | -------------------------- | -----------         | --------- | ---------------- | --------  | --------  |
|          |             | *RwTableTag*               |             |                    |                            |                     |           |                  |           |  |
| $counter | true        | TxAccessListAccount        | $txID       | $address           |                            |                     | $value    | 0                | $aux1     | $aux2 |
| $counter | true        | TxAccessListAccountStorage | $txID       | $address           |                            | $storageKey         | $value    | 0                | $aux1     | $aux2 |
| $counter | $isWrite    | TxRefund                   | $txID       |                    |                            |                     | $value    | 0                | $aux1     | $aux2 |
|          |             |                            |             |                    |                            |                     |           |                  |           |  |
|          |             |                            |             |                    | *AccountFieldTag*          |                     |           |                  |           |  |
| $counter | $isWrite    | Account                    |             | $address           | Nonce                      |                     | $value    | $valuePrev       | $aux1     | $aux2 |
| $counter | $isWrite    | Account                    |             | $address           | Balance                    |                     | $value    | $valuePrev       | $aux1     | $aux2 |
| $counter | $isWrite    | Account                    |             | $address           | CodeHash                   |                     | $value    | $valuePrev       | $aux1     | $aux2 |
|          |             |                            |             |                    |                            |                     |           |                  |           |  |
|          |             | *CallContext constant*     |             |                    | *CallContextFieldTag* (ro) |                     |           |                  |           |  |
| $counter | false       | CallContext                | $callID     |                    | RwCounterEndOfReversion    |                     | $value    | 0                | $aux1     | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | CallerId                   |                     | $value    | 0                | $aux1     | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | TxId                       |                     | $value    | 0                | $aux1     | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | Depth                      |                     | $value    | 0                | $aux1     | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | CallerAddress              |                     | $value    | 0                | $aux1     | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | CalleeAddress              |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | CallDataOffset             |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | CallDataLength             |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | ReturnDataOffset           |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | ReturnDataLength           |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | Value                      |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | IsSuccess                  |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | IsPersistent               |                     | $value    | 0               | $aux1      | $aux2 |
| $counter | false       | CallContext                | $callID     |                    | IsStatic                   |                     | $value    | 0               | $aux1      | $aux2 |
|          |             |                            |             |                    |                            |                     |            |            |                |  |
|          |             | *CallContext last callee*  |             |                    | *CallContextFieldTag* (rw) |                     |            |            |                |  |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeId               |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeReturnDataOffset |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | LastCalleeReturnDataLength |                     | $value     | 0               | $aux1     | $aux2 |
|          |             |                            |             |                    |                            |                     |            |            |                |  |
|          |             | *CallContext state*        |             |                    | *CallContextFieldTag* (rw) |                     |            |            |                |  |
| $counter | $isWrite    | CallContext                | $callID     |                    | IsRoot                     |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | IsCreate                   |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | CodeHash                   |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | ProgramCounter             |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | StackPointer               |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | GasLeft                    |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | MemorySize                 |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | CallContext                | $callID     |                    | ReversibleWriteCounter     |                     | $value     | 0               | $aux1     | $aux2 |
|          |             |                            |             |                    |                            |                     |            |            |                |  |
| $counter | $isWrite    | Stack                      | $callID     | $stackPointer      |                            |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | Memory                     | $callID     | $memoryAddress     |                            |                     | $value     | 0               | $aux1     | $aux2 |
| $counter | $isWrite    | AccountStorage             | $txID       | $address           |                            | $storageKey         | $value     | $valuePrev |
|          |             |                            |             |                    |                            |                     |            |            |                |  |
|          |             |                            |             |                    | *TxLogTag*                 |                     |            |            |                |  |
| $counter | true        | TxLog                      | $txID       | $logID,0           | Address                    | 0                   | $value     | 0               | $aux1     | $aux2 |
| $counter | true        | TxLog                      | $txID       | $logID,$topicIndex | Topic                      | 0                   | $value     | 0               | $aux1     | $aux2 |
| $counter | true        | TxLog                      | $txID       | $logID,$byteIndex  | Data                       | 0                   | $value     | 0               | $aux1     | $aux2 |
| $counter | true        | TxLog                      | $txID       | $logID,0           | TopicLength                | 0                   | $value     | 0               | $aux1     | $aux2 |
| $counter | true        | TxLog                      | $txID       | $logID,0           | DataLength                 | 0                   | $value     | 0               | $aux1     | $aux2 |
|          |             |                            |             |                    |                            |                     |            |                 |           |  |
|          |             |                            |             |                    | *TxReceiptTag*             |                     |            |                 |           |  |
| $counter | false       | TxReceipt                  | $txID       | 0                  | PostStateOrStatus          | 0                   | $value     | 0               | $aux1     | $aux2 |
| $counter | false       | TxReceipt                  | $txID       | 0                  | CumulativeGasUsed          | 0                   | $value     | 0               | $aux1     | $aux2 |
| $counter | false       | TxReceipt                  | $txID       | 0                  | LogLength                  | 0                   | $value     | 0               | $aux1     | $aux2 |

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

| Address | MPTProofType               | Key  | ValuePrev     | Value        | RootPrev  | Root  |
| ------- | ----------------------- | ---- | ------------- | ------------ | --------- | ----- |
| $addr   | NonceMod                | 0    | $noncePrev    | $nonceCur    | $rootPrev | $root |
| $addr   | BalanceMod              | 0    | $balancePrev  | $balanceCur  | $rootPrev | $root |
| $addr   | CodeHashMod             | 0    | $codeHashPrev | $codeHashCur | $rootPrev | $root |
| $addr   | NonExistingAccountProof | 0    | 0             | 0            | $root     | $root |
| $addr   | AccountDeleteMod        | 0    | 0             | 0            | $rootPrev | $root |
| $addr   | StorageMod              | $key | $valuePrev    | $value       | $rootPrev | $root |
| $addr   | NonExistingStorageProof | $key | 0             | 0            | $root     | $root |

## `Keccak Table`

See [tx_circuit.py](../src/zkevm_specs/tx_circuit.py)

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

The copy table consists of 9 columns, described as follows:

- **is_first**: a boolean value to indicate the first row in a copy event.
- **id**: could be `$txID`, `$callID`, `$codeHash` (RLC encoded).
- **addr**: indicates the address in the source data, could be memory address, byte index in the bytecode, tx call data, and tx log data. When the data type is `TxLog`, the address is the combination of byte index, `TxLogFieldTag.Data` tag, and `LogID`.
- **src_addr_end**: indicates the address boundary of the source data. Any data read from address greater than or equal to `AddressEnd` should be 0. Note `AddressEnd` is only valid for read operations or `q_step` is 1.
- **bytes_left**: indicates the number of bytes left to be copied.
- **rlc_acc**: indicates the RLC representation of an accumulator value over all write values.
- **rw_counter**: indicates the current RW counter at this row. This value will be used in the lookup to the `rw_table` when `Type` is  `Memory` or `TxLog`.
- **rwc_inc_left**: indicates how much the RW counter will increase in a copy event.
- **tag**: indicates tag which row depends as in `Bytecode`, `Memory`, `TxCalldata` or `TxLog`.

Unlike other lookup tables, the copy table is a virtual table. The lookup entry is not a single row in the table, and not every row corresponds to a lookup entry.
Instead, a lookup entry is constructed from the first two rows in each copy event as
`(is_first, id, addr, src_addr_end, bytes_left, rlc_acc, rw_counter, rwc_inc_left, tag)`, where `is_first` is 1 and `Column[1]` indicates the next row in the corresponding column.

The table below lists all of copy pairs supported in the copy table:
- Copy from Tx call data to memory (`CALLDATACOPY`).
- Copy from caller/callee memory to callee/caller memory (`CALLDATACOPY`, `RETURN` (not create), `RETURNDATACOPY`, `REVERT`).
- Copy from bytecode to memory (`CODECOPY`, `EXTCODECOPY`).
- Copy from memory to bytecode (`CREATE`, `CREATE2`, `RETURN` (create))
- Copy from memory to TxLog in the `rw_table` (`LOGX`)
- Copy from memory to RlcAcc (`SHA3`)

| is_first | id        | addr           | src_addr_end   | bytes_left | rlc_acc | rw_counter | rwc_inc_left | tag        |
|----------|-----------|----------------|----------------|------------|---------|------------|--------------|------------|
| 1        | $txID     | $byteIndex     | $cdLength      | $bytesLeft | $rlcAcc | -          | $rwcIncLeft  | TxCalldata |
| 0        | $callID   | $memoryAddress | -              | -          | $rlcAcc | $counter   | $rwcIncLeft  | Memory     |
|          |           |                |                |            | $rlcAcc |            |              |            |
| 1        | $callID   | $memoryAddress | $memoryAddress | $bytesLeft | $rlcAcc | $counter   | $rwcIncLeft  | Memory     |
| 0        | $callID   | $memoryAddress | -              | -          | $rlcAcc | $counter   | $rwcIncLeft  | Memory     |
|          |           |                |                |            | $rlcAcc |            |              |            |
| 1        | $callID   | $memoryAddress | $memoryAddress | $bytesLeft | $rlcAcc | $counter   | $rwcIncLeft  | Memory     |
| 0        | $codeHash | $byteIndex     | -              | -          | $rlcAcc | -          | $rwcIncLeft  | Bytecode   |
|          |           |                |                |            | $rlcAcc |            |              |            |
| 1        | $codeHash | $byteIndex     | $codeLength    | $bytesLeft | $rlcAcc | -          | $rwcIncLeft  | Bytecode   |
| 0        | $callID   | $memoryAddress | -              | -          | $rlcAcc | $counter   | $rwcIncLeft  | Memory     |
|          |           |                |                |            | $rlcAcc |            |              |            |
| 1        | $callID   | $memoryAddress | $memoryAddress | $bytesLeft | $rlcAcc | $counter   | $rwcIncLeft  | Memory     |
| 0        | $txID     | $byteIndex  \|\| TxLogData \|\| $logID | - | - | $rlcAcc | $counter | $rwcIncLeft  | TxLog      |

## Exponentiation Table

Proved by the Exponentiation circuit.

The exponentiation table is a virtual table within the exponentiation circuit assignments. An exponentiation operation `a ^ b == c (mod 2^256)` is broken down into steps that perform the exponentiation by squaring.

The following algorithm is used for exponentiation by squaring:
```py
def exp_by_squaring(x, n):
    if n = 0  then return  1
    if n = 1  then return  x
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

The exponentiation table consist of 11 columns, namely:
1. `is_step`: A boolean value to indicate whether or not the row is the start of a step representing the exponentiation trace.
2. `identifier`: An identifier (currently read-write counter at which the exponentiation table is looked up) to uniquely identify an exponentiation trace.
3. `is_last`: A boolean value to indicate the last row of the exponentiation trace's table assignments.
4. `base_limb[i]`: Four 64-bit limbs representing the integer base of the exponentiation operation.
5. `exponent_lo_hi[i]`: Two 128-bit low/high parts of an intermediate value that starts at the integer exponent.
6. `exponentiation_lo_hi[i]`: Two 128-bit low/high parts of an intermediate value that starts at the result of the exponentation operation.

The lookup entry is not a single row in the table, and not every row corresponds to a lookup entry. Instead, a lookup entry is constructed from the first 4 rows in each exponentiation event. For simplicity in the `specs` implementation, we combine all those rows into a single row. But in the `circuits` implementation, we try to lower the number of columns in exchange of increased number of rows.

Depending on the value of the `exponent` within the exponentiation operation, the `EXP` gadget will be handled by one of the below mentioned scenarios:
1. *Scenario #1* - Do no lookup if `exponent == 0` since `base ^ 0 == 1 (mod 2^256)`
2. *Scenario #2* Do no lookup if `exponent == 1` since `base ^ 1 == base (mod 2^256)`
3. *Scenario #3* Do 1 lookup to a row if `exponent == 2` since there is a single step in the exponentiation trace, i.e. `base ^ 2 == base * base (mod 2^256)`, implying that `is_first == is_last == 1` for this row.
4. *Scenario #4* Do 2 lookups to 2 different rows if `exponent > 2` since there are more than one steps in the exponentiation trace, i.e. a lookup to `is_last == 0` and a lookup to `is_last == 1`.

Consider `3 ^ 13 == 1594323 (mod 2^256)`. The exponentiation table assignment looks as follows:

| is_step | identifier | is_last | base_limb0 | base_limb1 | base_limb2 | base_limb3 | exponent_lo | exponent_hi | exponentiation_lo | exponentiation_hi |
|---------|------------|---------|------------|------------|------------|------------|-------------|-------------|-------------------|-------------------|
| 1       | $rwc       | 0       | 3          | 0          | 0          | 0          | 13          | 0           | 1594323           | 0                 |
| 1       | $rwc       | 0       | 3          | 0          | 0          | 0          | 12          | 0           | 531441            | 0                 |
| 1       | $rwc       | 0       | 3          | 0          | 0          | 0          | 6           | 0           | 729               | 0                 |
| 1       | $rwc       | 0       | 3          | 0          | 0          | 0          | 3           | 0           | 27                | 0                 |
| 1       | $rwc       | 1       | 3          | 0          | 0          | 0          | 2           | 0           | 9                 | 0                 |

For `exponent == 13`, i.e. Scenario #4 we do two lookups:
1. Lookup to first row:
```
Row(is_step=1, identifier=rwc, is_last=0, base_limbs=[3, 0, 0, 0], exponent_lo_hi=[13, 0], exponentiation_lo_hi=[1594323, 0])
```
2. Lookup to last row:
```
Row(is_step=1, identifier=rwc, is_last=1, base_limbs=[3, 0, 0, 0], exponent_lo_hi=[2, 0], exponentiation_lo_hi=[9, 0])
```

## Bn256 Table

Proved by the Bn256 circuit.

The bn256 table is a virtual table within the bn256 circuit assignments. There are four bn256 operations `ecRecover`, `ecAdd` and `ecMul`, `ecPairing`.

- **id**: could be `$callID`(RLC encoded).
- **tag**: indicates the type of bn256 operation, including `ecRecover`, `ecAdd` and `ecMul`, `ecPairing`.
- **input_length**: a input byte length of bn256 operation.
- **output_length**: a output byte length of bn256 operation.
- **input**: input for each bn256 operation.
- **input**: output for each bn256 operation.


| id | tag | input_length | output_length | input                                                          | output                                                                             |
|----|-----|--------------|---------------|----------------------------------------------------------------|------------------------------------------------------------------------------------|
| 1  | 2   | 4          | 2             | 0x00000000000000000000000000000001000000000000000000000000000000020000000000000000000000000000000100000000000000000000000000000002 | 0x37Ed60E69827d67879c9225527190df1650359a4b90d9A02Cc4E31b263Bf6910 |

The bn256 operation tag constrains output length and selects bn256 gadget.

| 0 Tag               | 1 Enum | 2 Input Length | 3 Output Length |
| ---                 | ---    | ---            | ---             |
| *Bn256OperationTag* |        |                |                 |
| ecRecover           | 0      | 4              | 1               |
| ecAdd               | 1      | 4              | 2               |
| ecMul               | 2      | 3              | 2               |
| ecPairing           | 3      | more than 4    | 1               |
