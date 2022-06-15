# Tables

For the zkevm we use the following dynamic and fixed tables for lookups to the EVM circuit.  The validity of the dynamic tables contents is proved by their own associated circuit.

Code spec at [table.py](../src/zkevm_specs/evm/table.py)

## `tx_table`

Proved by the tx circuit.

| 0 TxID | 1 Tag               | 2          | 3 value |
| ---    | ---                 | ---        | ---     |
|        | *TxContextFieldTag* |            |         |
| $TxID  | Nonce               | 0          | $value  |
| $TxID  | GasLo               | 0          | $value  |
| $TxID  | GasHi               | 0          | $value  |
| $TxID  | GasPrice            | 0          | $value  |
| $TxID  | CallerAddress       | 0          | $value  |
| $TxID  | CalleeAddress       | 0          | $value  |
| $TxID  | IsCreate            | 0          | $value  |
| $TxID  | Value               | 0          | $value  |
| $TxID  | CallDataLength      | 0          | $value  |
| $TxID  | TxSignHashLo        | 0          | $value  |
| $TxID  | TxSignHashHi        | 0          | $value  |
| $TxID  | CallData            | $ByteIndex | $value  |

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

| 0 *Rwc*  | 1 *IsWrite* | 2 *Tag* (0)                | 3 *Id* (1) | 4 *Address* (2)    | 5 *FieldTag* (3)           | 6 *StoKeyLo* (4) | 7 *StoKeyHi* (5) | 8 *val0*  | 9 *val1*   | 10 *Aux0*       |
| -------- | ----------- | -------------------------- | --------   | --------           | -------------------------- | -----------      | -----------      | --------- | ---------- | --------------- |
|          |             | *RwTableTag*               |            |                    |                            |                  |                  |           |            |                 |
| $counter | true        | TxAccessListAccount        | $txID      | $address           |                            |                  |                  | $val      | $valPrev   | 0               |
| $counter | true        | TxAccessListAccountStorage | $txID      | $address           |                            | $storageKeyLo    | $storageKeyHi    | $val      | $valPrev   | 0               |
| $counter | $isWrite    | TxRefund                   | $txID      |                    | Lo                         |                  |                  | $valLo    | $valLoPrev | 0               |
| $counter | $isWrite    | TxRefund                   | $txID      |                    | Hi                         |                  |                  | $valHi    | $valHiPrev | 0               |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
|          |             |                            |            |                    | *AccountFieldTag*          |                  |                  |           |            |                 |
| $counter | $isWrite    | Account                    |            | $address           | NonceLo                    |                  |                  | $valLo    | $valLoPrev | $commitValLo    |
| $counter | $isWrite    | Account                    |            | $address           | NonceHi                    |                  |                  | $valHi    | $valHiPrev | $commitValHi    |
| $counter | $isWrite    | Account                    |            | $address           | BalanceLo                  |                  |                  | $valLo    | $valLoPrev | $commitValLo    |
| $counter | $isWrite    | Account                    |            | $address           | BalanceHi                  |                  |                  | $valHi    | $valHiPrev | $commitValHi    |
| $counter | $isWrite    | Account                    |            | $address           | CodeHashLo                 |                  |                  | $valLo    | $valLoPrev | $commitValLo    |
| $counter | $isWrite    | Account                    |            | $address           | CodeHashHi                 |                  |                  | $valHi    | $valHiPrev | $commitValHi    |
| $counter | true        | AccountDestructed          |            | $address           |                            |                  |                  | $val      | $valPrev   | 0               |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
|          |             | *CallContext constant*     |            |                    | *CallContextFieldTag* (ro) |                  |                  |           |            |                 |
| $counter | false       | CallContext                | $callID    |                    | RwCounterEndOfReversion    |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | CallerId                   |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | TxId                       |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | Depth                      |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | CallerAddress              |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | CalleeAddress              |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | CallDataOffset             |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | CallDataLength             |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | ReturnDataOffset           |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | ReturnDataLength           |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | ValLo                      |                  |                  | $valLo    | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | ValHi                      |                  |                  | $valHi    | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | IsSuccess                  |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | IsPersistent               |                  |                  | $val      | 0          | 0               |
| $counter | false       | CallContext                | $callID    |                    | IsStatic                   |                  |                  | $val      | 0          | 0               |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
|          |             | *CallContext last callee*  |            |                    | *CallContextFieldTag* (rw) |                  |                  |           |            |                 |
| $counter | $isWrite    | CallContext                | $callID    |                    | LastCalleeId               |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | LastCalleeReturnDataOffset |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | LastCalleeReturnDataLength |                  |                  | $val      | 0          | 0               |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
|          |             | *CallContext state*        |            |                    | *CallContextFieldTag* (rw) |                  |                  |           |            |                 |
| $counter | $isWrite    | CallContext                | $callID    |                    | IsRoot                     |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | IsCreate                   |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | CodeHashLo                 |                  |                  | $valLo    | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | CodeHashHi                 |                  |                  | $valHi    | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | ProgramCounter             |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | StackPointer               |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | GasLeft                    |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | MemorySize                 |                  |                  | $val      | 0          | 0               |
| $counter | $isWrite    | CallContext                | $callID    |                    | ReversibleWriteCounter     |                  |                  | $val      | 0          | 0               |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
| $counter | $isWrite    | Stack                      | $callID    | $stackPointer      | Lo                         |                  |                  | $valLo    | $valLoPrev | 0               |
| $counter | $isWrite    | Stack                      | $callID    | $stackPointer      | Hi                         |                  |                  | $valHi    | $valHiPrev | 0               |
| $counter | $isWrite    | Memory                     | $callID    | $memoryAddress     |                            |                  |                  | $val      | $valPrev   | 0               |
| $counter | $isWrite    | AccountStorage             | $txID      | $address           | Lo                         | $storageKeyLo    | $storageKeyHi    | $valLo    | $valLoPrev | $commitValLo    |
| $counter | $isWrite    | AccountStorage             | $txID      | $address           | Hi                         | $storageKeyLo    | $storageKeyHi    | $valHi    | $valHiPrev | $commitValHi    |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
|          |             |                            |            |                    | *TxLogTag*                 |                  |                  |           |            |                 |
| $counter | true        | TxLog                      | $txID      | $logID,0           | Address                    | 0                | 0                | $val      | 0          | 0               |
| $counter | true        | TxLog                      | $txID      | $logID,$topicIndex | TopicLo                    | 0                | 0                | $valLo    | 0          | 0               |
| $counter | true        | TxLog                      | $txID      | $logID,$topicIndex | TopicHi                    | 0                | 0                | $valHi    | 0          | 0               |
| $counter | true        | TxLog                      | $txID      | $logID,$byteIndex  | Data                       | 0                | 0                | $val      | 0          | 0               |
| $counter | true        | TxLog                      | $txID      | $logID,0           | TopicLength                | 0                | 0                | $val      | 0          | 0               |
| $counter | true        | TxLog                      | $txID      | $logID,0           | DataLength                 | 0                | 0                | $val      | 0          | 0               |
|          |             |                            |            |                    |                            |                  |                  |           |            |                 |
|          |             |                            |            |                    | *TxReceiptTag*             |                  |                  |           |            |                 |
| $counter | false       | TxReceipt                  | $txID      | 0                  | PostStateOrStatus          | 0                | 0                | $val      | 0          | 0               |
| $counter | false       | TxReceipt                  | $txID      | 0                  | CumulativeGasUsed          | 0                | 0                | $val      | 0          | 0               |
| $counter | false       | TxReceipt                  | $txID      | 0                  | LogLength                  | 0                | 0                | $val      | 0          | 0               |

## `bytecode_table`

Proved by the bytecode circuit.

> - **Tag**: Tag whether the row represents the bytecode length or a byte in
>   the bytecode.

> - **isCode**: A boolean value to specify if the value is executable opcode or
>   the data portion of PUSH\* operations.

| 0 CodeHashLo | 1 CodeHashHi | 2 Tag              | 3 Index | 4 IsCode | 5 Value |
| ---          | ---          | ---                | ---     | ---      | ---     |
|              |              | *BytecodeFieldTag* |         |          |         |
| $codeHashLo  | $codeHashHi  | Length             | 0       | 0        | $value  |
| $codeHashLo  | $codeHashHi  | Byte               | $index  | $isCode  | $value  |
| ...          | ...          | ...                | ...     | ...      | ...     |
| $codeHashLo  | $codeHashHi  | Byte               | $index  | $isCode  | $value  |

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
| DifficultyLo           | 0      | $value  |
| DifficultyHi           | 0      | $value  |
| BaseFeeLo              | 0      | $value  |
| BaseFeeHi              | 0      | $value  |
| ChainID                | 0      | $value  |
| BlockHashLo            | 0..256 | $value  |
| BlockHashHi            | 0..256 | $value  |

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

| Target     | StRootLoPrev | StRootHiPrev | StRootLoCur | StRootHiCur | Address | Key    | ValuePrev       | ValueCur       |
| --------   | ---          | ---          | ---         | -------     | ----    | ----   | -------------   | ------------   |
| NonceLo    | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | 0      | $nonceLoPrev    | $nonceLoCur    |
| NonceHi    | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | 0      | $nonceHiPrev    | $nonceHiCur    |
| BalanceLo  | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | 0      | $balanceLoPrev  | $balanceLoCur  |
| BalanceHi  | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | 0      | $balanceHiPrev  | $balanceHiCur  |
| CodeHashLo | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | 0      | $codeHashLoPrev | $codeHashLoCur |
| CodeHashHi | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | 0      | $codeHashHiPrev | $codeHashHiCur |
| StorageLo  | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | $keyLo | $valueLoPrev    | $valueLoCur    |
| StorageHi  | $rootLoPrev  | $rootHiPrev  | $rootLoCur  | $rootHiCur  | $addr   | $keyHi | $valueHiPrev    | $valueHiCur    |

## `keccak_table`

Provided by the Keccak circuit.

| Enable | InputRLC  | InputLen  | Hash    |
| ---    | ---       | ---       | ---     |
| 0      | 0         | 0         | 0       |
| Lo     | $inputRLC | $inputLen | $hashLo |
| Hi     | $inputRLC | $inputLen | $hashHi |
