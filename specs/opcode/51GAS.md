# GAS opcode

## Procedure

The `GAS` opcode gets the amount of available gas, including the correspoding reduction for the cost of the instruction itself.

## EVM behaviour

The `GAS` opcode loads a 64-bit value for the available gas from the transaction context, and pushes it to the stack.

## Circuit behaviour

1. construct tx table
2. bus-mapping lookup for stack write operation
3. call context lookup (for `tx_id`)
4. tx lookup (for `gas_left`)

## Constraints

1. opId == 0x5A
2. State transition:
   - gc + 1 (1 stack write)
   - `stack_pointer` - 1
   - pc + 1
   - gas + 2
3. Lookups:
   - `gas` is on the top of stack
   - `tx_id` is in the call context table
   - `tx.gas_left` is in the tx table for above `tx_id`
4. Others:
   - `tx.gas_left == gas`

## Exceptions

1. Stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to [`gas.py`](src/zkevm_specs/evm/execution/gas.py)
