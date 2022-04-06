# block context op codes

## Procedure

The block context opcodes get the corresponding op data from current block context, and then push it to the stack. The `opcodes` contain `[COINBASE, TIMESTAMP, NUMBER, DIFFICULTY, GASLIMIT, BASEFEE]`.

## EVM behavior

The opcode loads the corresponding op n bytes of data from block context.
then push it to the stack.

n bytes length and RLC encoding:

- `COINBASE` 20 bytes length
- `TIMESTAMP` 8 bytes length
- `NUMBER` 8 bytes length
- `DIFFICULTY` 32 bytes length, RLC
- `GASLIMIT` 8 bytes length
- `BASEFEE` 32 bytes length, RLC

## Circuit behavior

1. construct block context table
2. do busmapping lookup for stack write operation
3. other implicit check: bytes length

## Constraints

1. opcodeId checks
   - opId == OpcodeId(0x41) for `COINBASE`
   - opId == OpcodeId(0x42) for `TIMESTAMP`
   - opId == OpcodeId(0x43) for `NUMBER`
   - opId == OpcodeId(0x44) for `DIFFICULTY`
   - opId == OpcodeId(0x45) for `GASLIMIT`
   - opId == OpcodeId(0x48) for `BASEFEE`
2. State transition:
   - gc + 1 (1 stack write)
   - stack_pointer - 1
   - pc + 1
   - gas + 2
3. Lookups:  2
   - `OP` is on the top of stack
   - `OP` is in the block context table
4. Others:

- `COINBASE` 20 bytes length
- `TIMESTAMP` 8 bytes length
- `NUMBER` 8 bytes length
- `DIFFICULTY` 32 bytes length, RLC
- `GASLIMIT` 8 bytes length
- `BASEFEE` 32 bytes length, RLC

## Exceptions

1. stack overflow: stack is full, stack pointer = 0
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/block_ctx.py`.
