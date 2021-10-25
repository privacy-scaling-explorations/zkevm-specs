# ADD and SUB op code

## Procedure

### EVM behavior

Pop two EVM words `a` and `b` from the stack. Compute
- if it's `ADD` opcode, compute `c = (a + b) % 2**256`, and push `c` back to the stack
- if it's `SUB` opcode, compute `c = (a - b) % 2**256`, and push `c` back to the stack

### Circuit behavior

The AddGadget takes argument of `a: [u8;32]`, `x: [u8;32]`, `y: [u8;32]`, `is_sub: bool`.

It always computes `y = (a + x) % 2**256`,

- when it's ADD (`is_sub == False`), we annotate stack as [a, x, ...] and [y, ...],
- when it's SUB (`is_sub == True`), we annotate stack as [a, y, ...] and [x, ...].

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x01) for `ADD`
   2. opId === OpcodeId(0x03) for `SUB`
2. state transition:
    - gc + 3
    - stack_pointer + 1
    - pc + 1
    - gas + 3
3. Lookups: 3 busmapping lookups
   - `a` is at the top of the stack
   - `b` is at the second position of the stack
   - `c`, the result, is at the new top of the stack

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/opcode/add.py`
