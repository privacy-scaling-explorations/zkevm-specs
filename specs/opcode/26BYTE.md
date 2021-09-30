# BYTE op code

## Procedure

The `BYTE` opcode retrieves a single byte from a value. This is done by popping two values, first the `index` and then the `value`, from the stack. The byte at position `index`, with the position starting at `0` at the MSB in `value`, will be copied to the LSB of `result`. `result` is then pushed on the stack.

## Constraints

1. opId = OpcodeId(0x1a)
2. state transition:
    - gc + 3 (2 stack reads + 1 stack write)
    - stack_pointer + 1
    - pc + 1
    - gas + 3
3. lookups: 3 busmapping lookups
    - `index` is at the top of the stack
    - `value` is at the new top of the stack
    - `result` is at the new top of the stack

## Exceptions

1. stack underflow: the stack is empty or only contains a single value
2. out of gas: the remaining gas is not enough

## Code

Please refer to `src/opcode/byte.py`