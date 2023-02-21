# ErrorGasUintOverflow state

## Procedure
this type of error occurs when mathematical operation detects overflow during calculating gas cost.

### EVM behavior
`ErrorGasUintOverflow` happends following situations.

- new memory size exceeds `0x1FFFFFFFE0`
- poped stack data exceeds uint64
- copy gas cost exceeds uint64
- sum of memory expanding gas cist and copy gas cost exceeds uint64
- call gas cost exceeds uint64

### Constraints
1. At least one of memory size, gas left and call gas cost exceed uint64
2. Current call must be failed

### Lookups
- Call Context lookup `TxId`
- Call Context lookup `IsSuccess`
- Call Context lookup `CallDataOffset`
- Call Context lookup `CallDataLength`

## Code

Please refer to `src/zkevm_specs/evm/execution/error_gas_uint_overflow.py`.
