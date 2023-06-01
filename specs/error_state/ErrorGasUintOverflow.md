# ErrorGasUintOverflow state

## Procedure

This type of error occurs when mathematical operation detects overflow during calculating gas cost.

### EVM behavior

`ErrorGasUintOverflow` happens when gas or memory calculation overflows in the following situations.

- [IntrinsicGas](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/state_transition.go#L67)
- for running interpreter: [Run](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/interpreter.go#L105)
- for CALL, CALLCODE, DELEGATECALL, STATICCALL: [callGas](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas.go#L37)

### Constraints

1. At least one of memory size, gas left and call gas cost exceed uint64
2. Current call must be failed
3. If it's a root call, it transits to `EndTx`.
4. If it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_gas_uint_overflow.py`.
