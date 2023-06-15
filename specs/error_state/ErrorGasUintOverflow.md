# ErrorGasUintOverflow state

## Procedure

This type of error occurs when mathematical operation detects overflow during calculating gas cost.

### EVM behavior

The `ErrGasUintOverflow` happens in

- [IntrinsicGas](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/state_transition.go#L67)
- [Run](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/interpreter.go#L105)
- [memoryCopierGas](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L65)
- [makeGasLog](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L223)
- [gasKeccak256](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L253)
- [gasCreate2](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L287)
- [gasCreateEip3860](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L305) 
- [gasCreate2Eip3860](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L321)
- [gasExpFrontier](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L338)
- [gasExpEIP158](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L351)
- [gasCall](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L364)
- [gasCallCode](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L399)
- [gasDelegateCall](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L424)
- [gasStaticCall](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas_table.go#L440)
- [callGas](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/gas.go#L37)

but when the `ErrGasUintOverflow` happens in [`dynamicGas`](https://github.com/ethereum/go-ethereum/blob/793f0f9ec860f6f51e0cec943a268c10863097c7/core/vm/interpreter.go#L218), the error turns out [`ErrOutOfGas`](https://github.com/ethereum/go-ethereum/blob/793f0f9ec860f6f51e0cec943a268c10863097c7/core/vm/interpreter.go#LL221C17-L221C28).

so we only need to care about follows case.

- [IntrinsicGas](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/state_transition.go#L67)
- [Run](https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/interpreter.go#L105)

More details are [here](https://github.com/privacy-scaling-explorations/zkevm-specs/pull/361#issuecomment-1478969271)

### Constraints

1. At least one of memory size, gas left and call gas cost exceed uint64
2. Current call must be failed
3. If it's a root call, it transits to `EndTx`.
4. If it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_gas_uint_overflow.py`.
