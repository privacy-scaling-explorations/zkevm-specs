# MSIZE op code

## Procedure

The `MSIZE` opcode return the memory size of the current contract and place it on the top of the stack.

## Constraints

1. opId = OpcodeId(0x59)
2. state transition:
    - gc + 1 (1 stack write)
    - stack_pointer - 1
    - pc + 1
    - gas + 2
3. lookups: `1` busmapping lookups
    - `value`  is pushed on top of the stack for `MSIZE`
    
## Exceptions

1. out of gas: the remaining gas is not enough
2. stack overflow: when stack is full, which means stack pointer is 0 before msize opcode

## Code

Please refer to `src/zkevm_specs/opcode/msize.py`.