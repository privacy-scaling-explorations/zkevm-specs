# RETURNDATACOPY opcode

## Procedure

The `RETURNDATACOPY` opcode pops `dest_offset`, `offset` and `size` from the stack.
It then copies `size` bytes of return data in the current environment from an offset `offset` to the memory at the address `return_data_offset`. For out-of-bound scenarios where `size > return_data_size - offset`, EVM reverts the current context.

The gas cost of `RETURNDATACOPY` opcode consists of two parts:

1. A constant gas cost: `3 gas`
2. A dynamic gas cost: cost of memory expansion and copying (variable depending on the `size` copied to memory)

### EVM behaviour

The `RETURNDATACOPY` opcode Copy output data from the previous call to memory.

### Circuit behaviour

1. Construct call context table in rw table.
2. Do a busmapping lookup for a stack read of dest_offset.
3. Do a busmapping lookup for a stack read of offset.
4. Do a busmapping lookup for a stack read of size.
5. Do a busmapping lookup for CallContext last Callee's Call_ID read.
4. Do a busmapping lookup for CallContext last Callee's ReturnDataLength read.
5. Do a busmapping lookup for CallContext last Callee's ReturnDataOffset read.
6. The copy of a dynamic number of bytes is verified by the CopyCircuit outside the `RETURNDATACOPY` gadget.

## Constraints

1. opId == 0x3E
2. State transition:
   - rw_counter -> rw_counter + 3 (stack read) + 2 (last callee info read) + size * 2 (copy == 1 mem read + 1 mem write)
   - stack pointer + 3
   - pc + 1
   - gas -> dynamic gas cost
   - memory_size
     - `prev_memory_size` if `size = 0`
     - `max(prev_memory_size, (memory_offset + size + 31) / 32)` if `size > 0`
3. Lookups: 6
   - `memory_offset` is at the 1st position of the stack
   - `data_offset` is at the 2nd position of the stack
   - `size` is at the 3rd position of the stack
   - `last_callee_id` is in last callee context
   - `return_data_offset` is in last callee context
   - `return_data_size` is in last callee context

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough
3. copy overflos: data_offset + size > return_data_size

## Code

Please refer to [returndatacopy.py](src/zkevm_specs/evm/execution/returndatacopy.py).
