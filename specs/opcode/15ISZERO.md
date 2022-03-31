# ISZERO opcode

## Procedure

Pop an EVM word `value` from the stack. If it is zero, push `1` back to the stack. Otherwise push `0` to stack.

## Constraints

1. state transition:
   - gc + 2 (1 stack read + 1 stack write)
   - stack_pointer + 0 (one pop and one push)
   - pc + 1
   - gas + 3
2. Lookups: 2 busmapping lookups
   - `value` is at the top of the stack
   - `result`, is at the new top of the stack

## Exceptions

1. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/opcode/iszero.py`
