# Tables

For the zkevm we use the following dynamic and fixed tables for lookups to the EVM circuit.  The validity of the dynamic tables contents is proved by their own associated circuit.

Code spec at [table.py](../src/zkevm_specs/evm_circuit/table.py)

Note: After the transition from encoding words as RLC to high and low parts,
all the columns that used to contain word_rlc have been doubled to contain
word_lo and word_hi.  To make this document more readable, we present words as
a single markdown column (for example *Value{Lo,Hi}*), but they correspond
to two circuit columns (for example *ValueLo* and *ValueHi*).

## `tx_table`

Proved by the tx circuit.
| 0 *TxId* | 1 *Tag*             | 2 *Index*  | *Value{Lo,Hi}* |
| ---      | ---                 | ---        | ---            |
|          | *TxContextFieldTag* |            |                |
| $TxID    | Nonce               | 0          | $value,0       |
| $TxID    | Gas                 | 0          | $value,0       |
| $TxID    | GasPrice            | 0          | $value{Lo,Hi}  |
| $TxID    | CallerAddress       | 0          | $value{Lo,Hi}  |
| $TxID    | CalleeAddress       | 0          | $value{Lo,Hi}  |
| $TxID    | IsCreate            | 0          | $value,0       |
| $TxID    | Value               | 0          | $value{Lo,Hi}  |
| $TxID    | CallDataLength      | 0          | $value,0       |
| $TxID    | CallDataGasCost     | 0          | $value,0       |
| $TxID    | TxSignHash          | 0          | $value{Lo,Hi}  |
| $TxID    | TxInvalid           | 0          | $value,0       |
| $TxID    | AccessListGasCost   | 0          | $value,0       |
| $TxID    | CallData            | $ByteIndex | $value,0       |
| $TxID    | Pad                 | 0          | 0,0            |

NOTE:
- `CallDataGasCost` and `TxSignHash` are values calculated by the verifier and used to reduce the circuit complexity.  They may be removed in the future.
- `TxInvalid` is a flag to tell the circuit which tx is invalid and should not be executed. We check `balance`, `nonce`, and `intrinsic gas` within `begin_tx`, `end_tx`, and `end_block` steps to make sure all txs being processed are valid, and all others are invalid and not executed. Invalid transactions go from the `begin_tx` state directly to the `end_tx` state and do not have any side effects.
- `AccessListGasCost` is the `accessList` gas cost of the tx, which equals to `sum([G_accesslistaddress + G_accessliststorage * len(TA[j]) for j in len(TA)])` (EIP 2930).

## `withdrawal_table`

Proved by the withdrawal circuit.

This circuit 
| 0 Withdrawal ID | 1 Validator ID | 2 Address      | 3 Amount      |
| -----------     | -------------  | -------------- | ------------- |
| $WithdrawalID   | $ValidatorID   | $value{Lo,Hi}  | $value{Lo,Hi} |

NOTE:
- `WithdrawalID` is increased monotonically, 64 bits.
- `ValidatorID`, 64 bits
- `Amount` is in Gwei, 64 bits

## `rw_table`

There are 14 columns in `rw_table`.
 - col. 0 (*Rwc*) is the read-write counter. 32 bits, starts at 1.
 - col. 1 (*IsWrite*) specify this row is for `read` or `write`.
 - col. 2 (*Tag*) is a tag for different contexts. The content for different *Tag*s are in col. 3 ~ col. 13.
 - col. 3 ~ 13 are the content for different *`Tag`* specified in col. 2 accordingly.
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
    - cols. {6,7} *StorageKey* is a Word and reserved for values
    - cols. {8,9} *value*, {10,11} *valuePrev*, {12,13} *initVal*, variable size, depending on Tag (key0) and FieldTag (key3) where appropriate.
        - (*value*) For *Tag* **Memory**: 8 bits
        - (*value*) For *Tag* **TxLog**: 8 bits
            - For *FieldTag* **Topic**: field size.
            - For *FieldTag* **Data**: 8 bits.

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

| 0 *Rwc*  | 1 *IsWrite* | 2 *Tag* k0                 | 3 *Id* k1 | 4 *Address* k2     | 5 *FieldTag* k3            | 6,7 *StoKey{Lo,Hi}* k4,k5 | 7,8 *Val{Lo,Hi}* | 9,10 *ValPrev{Lo,Hi}* | 11,12 *InitVal{Lo,Hi}* |
| -------- | ----------- | -------------------------- | --------  | --------           | -------------------------- | ------------------------- | ---------------- | --------------------- | ---------------------- |
|          |             | *Target*               |           |                    |                            |                           |                  |                       |                        |
| $counter | true        | TxAccessListAccount        | $txID     | $address           |                            |                           | $val,0           | $valPrev,0            |                        |
| $counter | true        | TxAccessListAccountStorage | $txID     | $address           |                            | $storageKey{Lo,Hi}        | $val,0           | $valPrev,0            |                        |
| $counter | $isWrite    | TxRefund                   | $txID     |                    |                            |                           | $val,0           | $valPrev,0            |                        |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
|          |             |                            |           |                    | *AccountFieldTag*          |                           |                  |                       |                        |
| $counter | $isWrite    | Account                    |           | $address           | Nonce                      |                           | $val,0           | $valPrev,0            | $committedValue,0      |
| $counter | $isWrite    | Account                    |           | $address           | Balance                    |                           | $val{Lo,Hi}      | $valPrev{Lo,Hi}       | $committedValue{Lo,Hi} |
| $counter | $isWrite    | Account                    |           | $address           | CodeHash                   |                           | $val{Lo,Hi}      | $valPrev{Lo,Hi}       | $committedValue{Lo,Hi} |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
|          |             | *CallContext constant*     |           |                    | *CallContextFieldTag* (ro) |                           |                  |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | RwCounterEndOfReversion    |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | CallerId                   |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | TxId                       |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | Depth                      |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | CallerAddress              |                           | $val{Lo,Hi}      |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | CalleeAddress              |                           | $val{Lo,Hi}      |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | CallDataOffset             |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | CallDataLength             |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | ReturnDataOffset           |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | ReturnDataLength           |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | Value                      |                           | $val{Lo,Hi}      |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | IsSuccess                  |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | IsPersistent               |                           | $val,0           |                       |                        |
| $counter | false       | CallContext                | $callID   |                    | IsStatic                   |                           | $val,0           |                       |                        |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
|          |             | *CallContext last callee*  |           |                    | *CallContextFieldTag* (rw) |                           |                  |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | LastCalleeId               |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | LastCalleeReturnDataOffset |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | LastCalleeReturnDataLength |                           | $val,0           |                       |                        |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
|          |             | *CallContext state*        |           |                    | *CallContextFieldTag* (rw) |                           |                  |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | IsRoot                     |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | IsCreate                   |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | CodeHash                   |                           | $val{Lo,Hi}      |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | ProgramCounter             |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | StackPointer               |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | GasLeft                    |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | MemorySize                 |                           | $val,0           |                       |                        |
| $counter | $isWrite    | CallContext                | $callID   |                    | ReversibleWriteCounter     |                           | $val,0           |                       |                        |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
| $counter | $isWrite    | Stack                      | $callID   | $stackPointer      |                            |                           | $val{Lo,Hi}      |                       |                        |
| $counter | $isWrite    | Memory                     | $callID   | $memoryAddress     |                            |                           | $val,0           |                       |                        |
| $counter | $isWrite    | AccountStorage             | $txID     | $address           |                            | $storageKey{Lo,Hi}        | $val{Lo,Hi}      | $valPrev{Lo,Hi}       | $committedValue{Lo,Hi} |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
|          |             |                            |           |                    | *TxLogTag*                 |                           |                  |                       |                        |
| $counter | true        | TxLog                      | $txID     | $logID,0           | Address                    |                           | $val{Lo,Hi}      |                       |                        |
| $counter | true        | TxLog                      | $txID     | $logID,$topicIndex | Topic                      |                           | $val{Lo,Hi}      |                       |                        |
| $counter | true        | TxLog                      | $txID     | $logID,$byteIndex  | Data                       |                           | $val,0           |                       |                        |
| $counter | true        | TxLog                      | $txID     | $logID,0           | TopicLength                |                           | $val,0           |                       |                        |
| $counter | true        | TxLog                      | $txID     | $logID,0           | DataLength                 |                           | $val,0           |                       |                        |
|          |             |                            |           |                    |                            |                           |                  |                       |                        |
|          |             |                            |           |                    | *TxReceiptTag*             |                           |                  |                       |                        |
| $counter | false       | TxReceipt                  | $txID     |                    | PostStateOrStatus          |                           | $val,0           |                       |                        |
| $counter | false       | TxReceipt                  | $txID     |                    | CumulativeGasUsed          |                           | $val,0           |                       |                        |
| $counter | false       | TxReceipt                  | $txID     |                    | LogLength                  |                           | $val,0           |                       |                        |

## `bytecode_table`

Proved by the bytecode circuit.

> - **Tag**: Tag whether the row represents the bytecode length or a byte in
>   the bytecode.

> - **isCode**: A boolean value to specify if the value is executable opcode or
>   the data portion of PUSH\* operations.

| 0,1 *CodeHash{Lo,Hi}* | 2 *Tag* | 3 *Index*          | 4 *IsCode* | 5 *Value* |
| ---                   | ---     | ---                | ---        | ---       |
|                       |         | *BytecodeFieldTag* |            |           |
| $codeHash{Lo,Hi}      | Length  | 0                  | 0          | $value    |
| $codeHash{Lo,Hi}      | Byte    | $index             | $isCode    | $value    |
| ...                   | ...     | ...                | ...        | ...       |
| $codeHash{Lo,Hi}      | Byte    | $index             | $isCode    | $value    |

In the case of an account without code, it can still have a row in the bytecode circuit to represent the `BytecodeFieldTag::Length` tag, with a `value = 0` and `codeHash = EMPTY_CODE_HASH`.

## `block_table`

Proved by the block circuit.

__Note that a generalisation is done by storing the ChainId field inside the block_table__
__when it should indeed live inside of the chain configuration section (which we don't have).__
__Hence the addition inside of the block_table.__

| 0 *Tag*                | 1 *Index* | 2 *Value{Lo,Hi}* |
| ---                    | ---       | ---              |
| *BlockContextFieldTag* |           |                  |
| Coinbase               | 0         | $value{Lo,Hi}    |
| GasLimit               | 0         | $value,0         |
| BlockNumber            | 0         | $value,0         |
| Time                   | 0         | $value,0         |
| PrevRandao             | 0         | $value{Lo,Hi}    |
| BaseFee                | 0         | $value{Lo,Hi}    |
| ChainID                | 0         | $value,0         |
| BlockHash              | 0..256    | $value{Lo,Hi}    |

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

The circuit can prove that updates to account nonces, balances, or storage slots are correct, or that an account's code hash is some particular value. Note that it is not possible to change the code hash for an account without deleting it and then recreating it.

| *Address* | *MPTProofType*          | *Key{Lo,Hi}* | *ValuePrev{Lo,Hi}*   | *Value{Lo,Hi}*      | *RootPrev{Lo,Hi}* | *Root{Lo,Hi}* |
| -------   | ----------------------- | ----         | -------------        | ------------        | ---------         | -----         |
| $addr     | NonceMod                | 0,0          | $noncePrev,0         | $nonceCur,0         | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |
| $addr     | BalanceMod              | 0,0          | $balancePrev{Lo,Hi}  | $balanceCur{Lo,Hi}  | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |
| $addr     | CodeHashMod             | 0,0          | $codeHashPrev{Lo,Hi} | $codeHashCur{Lo,Hi} | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |
| $addr     | NonExistingAccountProof | 0,0          | 0,0                  | 0,0                 | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |
| $addr     | AccountDeleteMod        | 0,0          | 0,0                  | 0,0                 | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |
| $addr     | StorageMod              | $key{Lo,Hi}  | $valuePrev{Lo,Hi}    | $valueCur{Lo,Hi}    | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |
| $addr     | NonExistingStorageProof | $key{Lo,Hi}  | 0,0                  | 0,0                 | $rootPrev{Lo,Hi}  | $root{Lo,Hi}  |

## `Keccak Table`

See [tx.py](../src/zkevm_specs/tx.py)

| *IsEnabled* | *InputRLC* | *InputLen*    | *Output{Lo,Hi}* |
| ---------   | ---------- | ------------- | --------------- |
| bool        | $input_rlc | $input_length | $output{Lo,Hi}  |

Column names in circuit:
- IsEnabled: `is_final`
- InputRLC: `data_rlc`
- InputLen: `length`
- OutputHi/Lo: `hash_hi/lo`


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

| is_first   | id{Lo,Hi}        | addr             | src_addr_end     | bytes_left   | rlc_acc   | rw_counter   | rwc_inc_left   | tag          |
| ---------- | -----------      | ---------------- | ---------------- | ------------ | --------- | ------------ | -------------- | ------------ |
| 1          | $txID,0          | $byteIndex       | $cdLength        | $bytesLeft   | $rlcAcc   | -            | $rwcIncLeft    | TxCalldata   |
| 0          | $callID,0        | $memoryAddress   | -                | -            | $rlcAcc   | $counter     | $rwcIncLeft    | Memory       |
|            |                  |                  |                  |              | $rlcAcc   |              |                |              |
| 1          | $callID,0        | $memoryAddress   | $memoryAddress   | $bytesLeft   | $rlcAcc   | $counter     | $rwcIncLeft    | Memory       |
| 0          | $callID,0        | $memoryAddress   | -                | -            | $rlcAcc   | $counter     | $rwcIncLeft    | Memory       |
|            |                  |                  |                  |              | $rlcAcc   |              |                |              |
| 1          | $callID,0        | $memoryAddress   | $memoryAddress   | $bytesLeft   | $rlcAcc   | $counter     | $rwcIncLeft    | Memory       |
| 0          | $codeHash{Lo,Hi} | $byteIndex       | -                | -            | $rlcAcc   | -            | $rwcIncLeft    | Bytecode     |
|            |                  |                  |                  |              | $rlcAcc   |              |                |              |
| 1          | $codeHash{Lo,Hi} | $byteIndex       | $codeLength      | $bytesLeft   | $rlcAcc   | -            | $rwcIncLeft    | Bytecode     |
| 0          | $callID,0        | $memoryAddress   | -                | -            | $rlcAcc   | $counter     | $rwcIncLeft    | Memory       |
|            |                  |                  |                  |              | $rlcAcc   |              |                |              |
| 1          | $callID,0        | $memoryAddress   | $memoryAddress   | $bytesLeft   | $rlcAcc   | $counter     | $rwcIncLeft    | Memory       |
| 0          | $txID,0          | $logAddress      | -                | -            | $rlcAcc   | $counter     | $rwcIncLeft    | TxLog        |

- $logAddress = $byteIndex || TxLogData || $logID

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

| IsStep    | Identifier   | IsLast    | BaseLimb0    | BaseLimb1    | BaseLimb2    | BaseLimb3    | Exponent{Lo,Hi} | Exponentiation{Lo,Hi} |
| --------- | ------------ | --------- | ------------ | ------------ | ------------ | ------------ | --------------- | --------------------- |
| 1         | $rwc         | 0         | 3            | 0            | 0            | 0            | 13,0            | 1594323,0             |
| 1         | $rwc         | 0         | 3            | 0            | 0            | 0            | 12,0            | 531441,0              |
| 1         | $rwc         | 0         | 3            | 0            | 0            | 0            | 6,0             | 729,0                 |
| 1         | $rwc         | 0         | 3            | 0            | 0            | 0            | 3,0             | 27,0                  |
| 1         | $rwc         | 1         | 3            | 0            | 0            | 0            | 2,0             | 9,0                   |

For `exponent == 13`, i.e. Scenario #4 we do two lookups:
1. Lookup to first row:
```
Row(is_step=1, identifier=rwc, is_last=0, base_limbs=[3, 0, 0, 0], exponent_lo_hi=[13, 0], exponentiation_lo_hi=[1594323, 0])
```
2. Lookup to last row:
```
Row(is_step=1, identifier=rwc, is_last=1, base_limbs=[3, 0, 0, 0], exponent_lo_hi=[2, 0], exponentiation_lo_hi=[9, 0])
```
