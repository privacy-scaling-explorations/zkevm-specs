# ErrorOutOfGasConstant state

## Procedure
### EVM behavior
For Call opcode, there are multiple kinds of gas consumes:
1. memory expansion gas cost
    - 
2. sdjsdj
3. sdjksjd

```
GAS_COST_WARM_ACCESS := 100
GAS_COST_ACCOUNT_COLD_ACCESS := 2600
GAS_COST_CALL_EMPTY_ACCOUNT := 25000
GAS_COST_CALL_WITH_VALUE := 9000
gas_cost = (
    GAS_COST_WARM_ACCESS
    + GAS_COST_WARM_ACCESS if is_warm_access else GAS_COST_ACCOUNT_COLD_ACCESS
    + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_CALL_EMPTY_ACCOUNT)
    + memory_expansion_gas_cost
)
```

1. If it's a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.


### Constraints
1. `gas_left < gas_cost`.
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`.
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- 1 Call Context lookup `CallContextFieldTag.IsSuccess`.
- 1 Call Context lookup `CallContextFieldTag.IsPersistent`s. 

## Code

Please refer to `src/zkevm_specs/evm/execution/oog_call.py`.
