# CALLDATASIZE opcode

## Procedure

The `CALLDATASIZE` opcode gets the call data size (msg.data.size) from the current call.

## EVM behaviour

The `CALLDATASIZE` opcode loads a `u64` (5 bytes of data) from call context ->
call data length, then pushes the `u64` to the stack.

## Circuit behaviour

1. Construct call context table in rw table
2. Do busmapping lookup for call context call data length read operation
3. Do busmapping lookup for stack write operation

## Constraints

1. opId = 0x36
2. State transition:
   - gc + 2 (1 stack write, 1 call context read)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups: 2
   - `u64` is in the rw table {call context, call ID, call data length}
   - `u64` is on top of stack

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/calldatasize.py`.
