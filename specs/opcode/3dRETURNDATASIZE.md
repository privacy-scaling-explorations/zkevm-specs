# RETURNDATASIZE opcode

## Procedure

### EVM behaviour

The `RETURNDATASIZE` opcode gets size of output data from the previous call from the current environment.

### Circuit behaviour

1. Construct call context table in rw table.
2. Do a busmapping lookup for CallContext last Call's ReturnDataLength  read.
3. Do a busmapping lookup for a stack write operation corresponding to the RETURNDATASIZE result.

## Constraints

1. opId == 0x3D
2. State transition:
   - gc + 2
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups: 2
   - ReturnDataLength is in the rw table {call context, call ID, ReturnDataLength}.
   - ReturnDataLength is on top of stack.

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to [returndatasize.py](src/zkevm_specs/evm/execution/returndatasize.py).
