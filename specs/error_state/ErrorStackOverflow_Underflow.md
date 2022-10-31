# ErrorStackOverflow & underflow state

## Procedure
### EVM behavior
stack overflow and underflow error can happen within any step which involves stack operation.
each op code have fixed `minStack` & `maxStack`.  if current stack length < `minStack`, underflow error
happens, if current stack length > `maxStack`, overflow error happens.

when any one type error occurs:
1. If it's a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.

### Circuit behavior 
1. in order to get each step(op code)'s `minStack` & `maxStack` value, construct new fixed table
called `opcode_stack` table which holds the data.
2. look up `opcode_stack` table to retrieve current executing step's stack info(`minStack` & `maxStack`) 
3. combine stack overflow & underflow circuit into one, need to check `is_stack_overflow` and `is_stack_underflow`
is bool and only one is true at the mean while.
3. common error handling:
  - If it's a root call, it transits to `EndTx`, and the call's `IsPersistent` must be false 
  - if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_stack_overflow_underflow.py`.
