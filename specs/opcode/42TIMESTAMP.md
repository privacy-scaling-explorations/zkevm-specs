# Timestamp op code

## Procedure

The `TIMESTAMP` opcode pushes the timestamp of the current block onto the stack.

## EVM behavior

The `TIMESTAMP` opcode loads a `timestamp` (8 bytes of data) from the block context and then
pushes it onto the stack.

## Circuit behavior

1. construct block context table
2. do busmapping lookup for stack write operation
3. other implicit check: bytes length

## Constraints

1. opId = 0x42
2. State transition:
   - gc + 1 (1 stack write)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups:  2
   - `timestamp` is on the top of stack
   - `timestamp` is in the block context table
4. Others:
   - `timestamp` fits into 8 bytes

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/block_timestamp.py`.
