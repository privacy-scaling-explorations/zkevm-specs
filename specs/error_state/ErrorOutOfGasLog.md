# ErrorOutOfGasLog state

## Procedure
### EVM behavior
use `LOGN` denotes [log0, .., log4]. `N` stands for `topic_count` of circuit, that is 
`N = topic_count = opcode - Opcode.LOG0`.
For this gadget, the core is to calculate gas required as following:

`  let gas_cost =  GAS_COST_LOG
        + GAS_COST_LOG * (opcode - Opcode.LOG0)
        + GAS_COST_LOGDATA * msize
        + memory_expansion_gas`

### Constraints
1. stack reads `mstart`, `msize` for gas calculation
2. `gas_left < gas_cost`.
3. error common constraint:
  - current call must be failed.
  - rw_counter_end_of_reversion constraint
  - If it's a root call, it transits to `EndTx`. 
  - if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code
    
Please refer to `src/zkevm_specs/evm/execution/error_oog_log.py`.