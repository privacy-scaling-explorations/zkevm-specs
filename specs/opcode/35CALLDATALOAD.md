# CALLDATALOAD opcode

## Procedure

The `CALLDATALOAD` opcode gets input data of current environment.

## EVM Behaviour

Stack input is the byte offset to read call data from. Stack output is a 32-byte value starting from the given offset of the call data. All bytes after the end of the call data are set to `0`.

## Circuit Behaviour

1. Do busmapping lookup for stack read operation.
2. Construct call context table in RW table (for `tx.id`).
3. Construct tx context table in RW table (for every single byte of `tx.calldata`).
4. Do busmapping lookup for call context `txid` read operation.
5. Do busmapping lookup for tx context `calldata` read operation (for each one of the 32 bytes of the stack output).
6. Do busmapping lookup for stack write operation.

## Constraints

1. opId == 0x35
2. State Transition:
   - gc + 3 (1 stack read, 1 call context read, 1 stack write)
   - stack_pointer unchanged
   - pc + 1
   - gas - 3
3. Lookups:
   - for index `i in range(32)`: `stack_top[i]` is in the RW table {tx context, call data, i}

## Exceptions

1. Stack overflow: stack is full, stack pointer = 0
2. Out of gas: remaining gas is not enough for this opcode

## Code

Please refer to `src/zkevm_specs/evm/execution/calldataload.py`.
