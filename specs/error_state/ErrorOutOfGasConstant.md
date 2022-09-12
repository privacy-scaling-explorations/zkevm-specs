# ErrorOutOfGasConstant state

## Procedure
For opcodes which have non-zero constant gas cost, this type of error occurs when gas left of 
current step is less than the required constant gas.

### EVM behavior

1. If it's a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.

### Constraints
1. `remaining_gas_left < step_constant_gas_required`.
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`, and the call's `IsPersistent` must be false
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- 1 Call Context lookup `CallContextFieldTag.IsSuccess`.
- 1 Call Context lookup `CallContextFieldTag.IsPersistent` (Only if Current instruction is root.). 

## Code

Please refer to `src/zkevm_specs/evm/execution/oog_constant.py`.
