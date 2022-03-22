# CODECOPY opcode

## Procedure

The `CODECOPY` opcode pops `memory_offset`, `code_offset` and `size` from the stack.
It then copies `size` bytes of code running in the current environment from an offset `code_offset` to the memory at the address `memory_offset`. For out-of-bound scenarios where `size > len(code) - code_offset`, EVM pads 0 to the end of the copied bytes.

The gas cost of `CODECOPY` opcode consists of two parts:

1. A constant gas cost: `3 gas`
2. A dynamic gas cost: cost of memory expansion and copying (variable depending on the `size` copied to memory)

## Circuit Behaviour

`CODECOPY` makes use of the internal execution step `CopyCodeToMemory` and loops over these steps iteratively until there are no more bytes to be copied. The `CODECOPY` circuit itself only constrains the values popped from stack and call context/account read lookups.

The gadget then transits to the internal state of `CopyCodeToMemory`.

## Constraints

1. opId = 0x39
2. State Transitions:
   - rw_counter -> rw_counter + 3 (3 stack reads)
   - stack_pointer -> stack_pointer + 3
   - pc -> pc + 1
   - gas -> 3 + dynamic_cost (memory expansion and copier cost when `size > 0`)
   - memory_size
     - `prev_memory_size` if `size = 0`
     - `max(prev_memory_size, (memory_offset + size + 31) / 32)` if `size > 0`
3. Lookups:
   - `memory_offset` is at the top of the stack
   - `code_offset` is at the second position of the stack
   - `size` is at the third position of the stack
   - `code_size` from the bytecode table

## Exceptions

1. Stack Underflow: `1021 <= stack_pointer <= 1024`
2. Out-of-Gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/codecopy.py`
