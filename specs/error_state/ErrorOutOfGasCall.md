# ErrorOutOfGasConstant state

## Procedure
### EVM behavior
For this gadget, the core is to calculate gas required, there are multiple kinds of gas
consumes in call: 
1. memory expansion gas cost
2. gas cost if new account creates
3. transfer fee if has value
4. account access list cost（warm/cold）

below is the total gas cost calculation which from [`Call` Spec](../opcode/F1CALL.md).
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

### Constraints
1. `gas_left < gas_cost`.
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`.
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/oog_call.py`.
