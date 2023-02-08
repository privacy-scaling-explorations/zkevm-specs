# ErrorUintOverflow state

## Procedure
this type of error occurs when mathematical operation detects uint64 overflow during calculating gas cost.

### EVM behavior
`ErrorUintOverflow` happends following situations.

- new memory size exceeds `0x1FFFFFFFE0`
- poped stack data exceeds uint64
- copy gas cost exceeds uint64
- sum of memory expanding gas cist and copy gas cost exceeds uint64
- call gas cost exceeds uint64

### Constraints
1. At least one of memory size, gas left and call gas cost exceed uint64
2. Current call must be failed.

### Lookups
- Call Context lookup `CallContextFieldTag.TxId`.
- Call Context lookup `CallContextFieldTag.IsSuccess`.
- Call Context lookup `CallContextFieldTag.MemorySize`.
- Call Context lookup `CallContextFieldTag.GasLeft`.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_gas_uint_overflow.py`.
