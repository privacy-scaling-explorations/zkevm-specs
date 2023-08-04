# ErrorReturnDataOutOfBound state

## Procedure

This type of error only occurs when executing op code is `RETURNDATACOPY`.

### EVM behavior

The `RETURNDATACOPY` opcode pops `memOffset`,`dataOffset`, and `length` from the stack. A return data out of bound error is thrown if one of the following condition is met: 
1. `dataOffset`is u64 overflow, 
2. `dataOffset` + `length` is u64 overflow,
3. `dataOffset` + `length` is larger than the length of last callee's return data.

### Constraints
1. current opcode is `RETURNDATACOPY`
2. at least one of below conditions is met:
   -  `dataOffset`is u64 overflow, 
   - `dataOffset` + `length` is u64 overflow
   - `dataOffset` + `length` is larger than the length of last callee's return data
3. common error constraints: 
  - current call fails. 
  - constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.
  - If it's a root call, it transits to `EndTx`.
  - if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

  Please refer to src/zkevm_specs/evm_circuit/execution/error_return_data_out_of_bound.py