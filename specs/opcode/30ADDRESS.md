# ADDRESS opcode

## Procedure

The `ADDRESS` opcode gets the address of currently executing account.

## EVM behaviour

The `ADDRESS` opcode loads the callee address (20 bytes of data) from call
context, then pushes this address to the stack.

## Circuit behaviour

1. Construct call context table in rw table
2. Do busmapping lookup for call context callee read operation
3. Do busmapping lookup for stack write operation

## Constraints

1. opId = 0x30
2. State transition:
   - gc + 2 (1 stack write, 1 call context read)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups: 2
   - `address` is in the rw table {call context, call ID, callee}
   - `address` is on top of stack

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/address.py`.
