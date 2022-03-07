# Number op code

## Procedure

The `NUMBER` opcode get the block number from the current block context, and then push it onto the stack.

## EVM behavior

The `NUMBER` opcode loads a `number` (32 bytes of data) from the current block context, and then
pushes it onto the stack.

## Circuit behavior

1. construct block context table
2. do busmapping lookup for stack write operation

## Constraints

1. opId = 0x43
2. State transition:
   - gc + 1 (1 stack write)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups:  2
   - `number` is on the top of stack
   - `number` is in the block context table

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/block_number.py`.
