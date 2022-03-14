# SELFBALANCE opcode

## Procedure

The `SELFBALANCE` opcode pushes the balance (32 bytes of data) of the currently executing address onto the stack.

## Circuit behaviour

1. Construct call context table in rw table
2. Do busmapping lookup for stack write operation

## Constraints

1. opId = 0x47
2. State transition:
   - gc + 3 (1 stack write, 1 account balance read, and 1 callee address read)
   - stack_pointer - 1
   - pc + 1
   - gas + 5
3. Lookups: 3
   - `callee_address` is the callee address of the call context
   - `self_balance` is the balance of `callee_address`
   - `self_balance` is on the top of stack

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/selfbalance.py`.
