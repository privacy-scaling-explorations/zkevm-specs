# CHAINID opcode

## Procedure

The `CHAINID` opcode gets the chain id where a transaction is meant executed at.

## EVM behaviour

The `CHAINID` opcode loads a 256-bit value from the Tx context (the chain id), and pushes it to the stack.

## Circuit behaviour

1. Construct Tx Context table
2. Bus-mapping lookup for stack write operation

## Constraints

1. opId == 0x46
2. State transition:
   - gc + 2 (1 stack write + 1 Call Context read)
   - `stack_pointer` - 1
   - pc + 1
   - gas + 2
3. Lookups:
   - `tx_id` is on current call context
   - `chainid` is on the top of stack
   - `chainid` is in the transaction context table

## Exceptions

1. Stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to [`chainid.py`](src/zkevm_specs/evm/execution/chainid.py)
