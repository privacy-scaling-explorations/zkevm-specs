# RETURNDATACOPY opcode

## Procedure

### EVM behaviour

The `RETURNDATACOPY` opcode Copy output data from the previous call to memory.

### Circuit behaviour

1. Construct call context table in rw table.
2. Do a busmapping lookup for CallContext last Call's ReturnDataLength  read.
3. Do a busmapping lookup for a stack write operation corresponding to the RETURNDATACOPY result.

## Constraints

1. opId == 0x3E
2. State transition:
   - rw_counter -> rw_counter + 3 (stack read) + 2 (last callee info read) + size * 2 (copy == 1 mem read + 1 mem write)
   - stack pointer + 3
   - pc + 1
   - gas -> dynamic gas cost
3. Lookups: 5
   - `memory_offset` is at the 1st position of the stack
   - `data_offset` is at the 2nd position of the stack
   - `size` is at the 3rd position of the stack
   - `return_data_offset` is in last callee context
   - `return_data_size` is in last callee context

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough
3. copy overflos: data_offset + size > return_data_size

## Code

Please refer to [RETURNDATACOPY.py](src/zkevm_specs/evm/execution/RETURNDATACOPY.py).
