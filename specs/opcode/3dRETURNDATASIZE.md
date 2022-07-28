# RETURNDATASIZE opcode

## Procedure

### EVM behaviour

The `RETURNDATASIZE` opcode gets size of output data from the previous call from the current environment.

### Circuit behaviour

1. Construct call context table in rw table
2. Do busmapping lookup for call context last call return data length read operation
3. Do busmapping lookup for stack write operation

## Constraints

1. opId == 0x3D
2. State transition:
   - gc + 2
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

Please refer to `src/zkevm_specs/evm/execution/returndatasize.py`.
