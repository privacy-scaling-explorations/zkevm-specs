# CALLVALUE opcode

## Procedure

The `CALLVALUE` opcode gets the call value (msg.value) from the current call.

## EVM behaviour

The `CALLVALUE` opcode loads a `word` (32 bytes of data) from call context ->
call value, then pushes the `word` to the stack.

## Circuit behaviour

1. Construct call context table in rw table
2. Do busmapping lookup for call context call value read operation
3. Do busmapping lookup for stack write operation

## Constraints

1. opId = 0x34
2. State transition:
   - gc + 2 (1 stack write, 1 call context read)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups: 2
   - `word` is in the rw table {call context, call ID, call value}
   - `word` is on top of stack

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/callvalue.py`.
