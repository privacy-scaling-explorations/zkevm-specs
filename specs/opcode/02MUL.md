# MUL op code

## Procedure

We followed the approch of [Multi-Limbs Multiplication](https://hackmd.io/HL0QhGUeQoSgIBt2el6fHA), with some notes:

1. we consider there should be a trivial mistake in the original link which claimed the range of v0 and v1 is `[0, 2^64]` (they should be in the range of `[0, 2^66]`).

2. Ensuring v0 and v1 do not exceed the scalar field after being mutipled by 2^128 is enough. In our code v0 and v1 are constrainted by the combination of 9 bytes (each cell being constrainted by 8-bit range table) so they are constrainted to a slightly relaxed range of `[0, 2^72)`. Our approach use 3 evm words and 22 cells (totally 118 cells).

### EVM behavior

Pop two EVM words `a` and `b` from the stack. Compute `c = (a * b) % 2**256`, and push `c` back to the stack

### Circuit behavior

The MulGadget takes argument of `a: [u8;32]`, `x: [u8;32]`, `y: [u8;32]`.

It always computes `y = (a * x) % 2**256`, annotate stack as \[a, x, ...\] and \[y, ...\]

## Constraints

1. state transition:
   - gc + 3
   - stack_pointer + 1
   - pc + 1
   - gas + 5
2. Lookups: 3 busmapping lookups
   - `a` is at the top of the stack
   - `b` is at the second position of the stack
   - `c`, the result, is at the new top of the stack

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/opcode/mul.py`
