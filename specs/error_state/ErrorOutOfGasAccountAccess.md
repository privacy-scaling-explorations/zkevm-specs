# ErrorOutOfGasAccountAccess state

## Procedure

Handle the corresponding out of gas errors for `BALANCE`, `EXTCODESIZE`, and `EXTCODEHASH` opcodes which possibly touches an extra account.

### EVM behavior

For the current `go-ethereum` code, the out of gas error may occur for `constant gas` or `dynamic gas`. The gas cost is calculated as:

```
gas_cost = constant_gas + dynamic_gas
```

The constant gas costs are the same for `BALANCE`, `EXTCODESIZE`, and `EXTCODEHASH`.

```
constant_gas = 0
```

The calculation of the dynamic gas costs of `BALANCE`, `EXTCODESIZE`, and `EXTCODEHASH` is the same. It depends on cold and warm access.

```
if is_warm:
    dynamic_gas = 100
else:
    dynamic_gas = 2600
```

### Constraints

1. Current opcode is one of `BALANCE`, `EXTCODESIZE`, and `EXTCODEHASH`.
2. Constrain `gas_left < gas_cost`.
3. Current call must fail.
4. If it's a root call, it transits to `EndTx`.
5. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
6. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_oog_account_access.py`.
