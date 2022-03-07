# POP opcode

## Procedure

A stack initalize empty with stack pointer to 1024, pop operation can only happen when stack is not empty, and it will increase by 1 of stack pointer.

Even the popped value will never be used, it still does lookup to ensure the stack pointer is in range, since we don't explicitly verify stack pointer is in range each step, we instead let state circuit to verify that.

## Constraints

1. opId = OpcodeId(0x50)
2. state transition:
   - gc + 1
   - stack_pointer + 1
   - pc + 1
   - gas + 2
3. Lookups: 1 busmapping lookups
   - A value is indeed at the top of the stack

## Exceptions

1. stack underflow: when stack is empty
2. gas out: remaining gas is not enough

## Code

Please refer to `src/zkevm-specs/opcode/stack.py`.
