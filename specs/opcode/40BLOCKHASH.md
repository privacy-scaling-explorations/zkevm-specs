# BLOCKHASH opcode

## Procedure

The `BLOCKHASH` opcode pops `block_number` off the stack and pushes the hash from chosen block. If the chosen block number is not in valid range (last 256 blocks, not including current block), it will push 0 onto the stack.

## Constraints

1. opId == 0x40
2. State transition:
    - gc + 2 (1 stack read + 1 stack write)
    - stack_pointer + 0 (one pop and one push)
    - pc + 1
    - gas + 20
3. Lookups: 3
    - `block_number` is popped from the stack.
    - `current_block_number` is in the block context table.
    - `block_hash` is in the block context table.
4. Additional Constraint
    - `block_number` should be in valid range.

## Exceptions

1. stack underflow: if the stack starts empty
2. out of gas: remaining gas is not enough

## Code

Please refer to 'src/zkevm-specs/evm/execution/blockhash.py'
