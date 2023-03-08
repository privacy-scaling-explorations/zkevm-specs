# ErrorGasUintOverflow state

## Procedure

This type of error occurs when mathematical operation detects overflow during calculating gas cost.

### EVM behavior

`ErrorGasUintOverflow` happends following situations.

- [new memory size exceeds `0x1FFFFFFFE0`](https://github.com/ethereum/go-ethereum/blob/793f0f9ec860f6f51e0cec943a268c10863097c7/core/vm/gas_table.go#L38)
- [poped stack data exceeds uint64](https://github.com/ethereum/go-ethereum/blob/793f0f9ec860f6f51e0cec943a268c10863097c7/core/vm/gas_table.go#L73)
- [eip2028 gas check fails](https://github.com/ethereum/go-ethereum/blob/793f0f9ec860f6f51e0cec943a268c10863097c7/core/state_transition.go#L146)
- copy gas cost exceeds uint64
- sum of memory expanding gas cost and copy gas cost exceeds uint64
- call, log, keccak256 and create, create2 gas cost exceeds uint64

### Constraints

1. At least one of memory size, gas left and call gas cost exceed uint64
2. Current call must be failed
3. If it's a root call, it transits to `EndTx`.
4. If it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups

- Call Context lookup `TxId`
- Call Context lookup `IsSuccess`
- Call Context lookup `CallDataOffset`
- Call Context lookup `CallDataLength`

## Code

Please refer to `src/zkevm_specs/evm/execution/error_gas_uint_overflow.py`.
