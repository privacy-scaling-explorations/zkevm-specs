# ORIGIN opcode

## Procedure

The `ORIGIN` opcode gets the execution origination address (tx.origin).

## EVM behaviour

The `ORIGIN` opcode loads the sender address (20 bytes) of the transaction that originated this execution, then pushes the address to the stack.

## Circuit behaviour

1. Lookup call context in rw table for the txID
2. Lookup txID in Tx Table for the CallerAddress
3. Lookup stack write operation for the address

## Constraints

1. opId = 0x32
2. State transition:
   - gc + 2 (1 stack write, 1 call context read)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups: 3
   - `tx_id` is on current call context
   - `address` is in the Tx Table
   - `address` is on the top of stack

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to [`origin.py`](src/zkevm_specs/evm/execution/origin.py)
