# RETURNDATACOPY opcode

## Procedure

The `RETURNDATACOPY` opcode pops `dest_offset`, `offset` and `size` from the stack.
It then copies `size` bytes of return data in the current environment from `return_data_offset` at an `offset` to the memory at address `dest_offset`. For out-of-bound scenarios where `size > return_data_size - offset`, EVM reverts the current context.

The gas cost of `RETURNDATACOPY` opcode consists of two parts:

1. A constant gas cost: `3 gas`
2. A dynamic gas cost: cost of memory expansion and copying (variable depending on the `size` copied to memory)

### EVM behaviour

The `RETURNDATACOPY` opcode copies output data from the previous call to memory. If there is no previous call, the length of `RETURNDATACOPY` is bounded to 0 (returndatasize). Evm checks gas, stack and length boundary when copying, and reverts context if any exception happens.

### Circuit behaviour

1. Do a busmapping lookup for a stack read of dest_offset.
2. Do a busmapping lookup for a stack read of offset.
3. Do a busmapping lookup for a stack read of size.
4. Do a busmapping lookup for a CallContext read of last Callee's ID.
5. Do a busmapping lookup for a CallContext read of last Callee's ReturnDataLength.
6. Do a busmapping lookup for a CallContext read of last Callee's ReturnDataOffset.
7. Do a CopyTable lookup to verify the copy of bytes. The copy of a dynamic number of bytes is verified by the CopyCircuit outside the `RETURNDATACOPY` gadget.

## Constraints

1. opId == 0x3E
2. State transition:
   - rw_counter -> rw_counter + 3 (stack read) + 3 (last callee id & return data param read) + size * 2 (copy == 1 mem read + 1 mem write)
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

1. stack underflow: `1022 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough
3. copy overflow: data_offset + size > return_data_size

## Code

Please refer to [returndatacopy.py](src/zkevm_specs/evm/execution/returndatacopy.py).
