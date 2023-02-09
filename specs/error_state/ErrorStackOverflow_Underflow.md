# ErrorStackOverflow & underflow state

## Procedure
### EVM behavior
stack overflow and underflow error can happen within any step which involves stack operation.
each op code have fixed `min_stack_pointer` & `max_stack_pointer`.  if current stack pointer < `min_stack_pointer`, 
overflow error happens, if current stack pointer > `max_stack_pointer`, underflow error happens.

when any one type error occurs:
1. If it's a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.

### Circuit behavior

1. Do a bytecode lookup to get `opcode`.
2. Do a fixed lookup for `FixedTableTag.ResponsibleOpcode` with `opcode` and auxiliary `stack_pointer` to make sure it's indeed in pre-built pairs of `ErrorStack`.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_stack.py`.
