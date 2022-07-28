# CODESIZE opcode

## Procedure

### EVM behaviour

The `CODESIZE` opcode pushes the size of code running in the current environment to the top of the stack.

### Circuit behaviour

1. Lookup the code size from the bytecode table
2. Do busmapping lookup for stack write operation

## Constraints

1. opId = 0x38
2. State transition:
   - gc + 1 (1 stack write)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups: 2
   - `codesize` (bytecode_length) from the bytecode table
   - `codesize` is on top of stack

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/codesize.py`.
