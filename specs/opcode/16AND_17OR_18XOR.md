# AND, OR, XOR opcodes

## Procedure

Pop two EVM words `a` and `b` from the stack, and the output `c` is pushed to
the stack.

`a`, `b`, and `c` are all EVM words. We break three EVM words into 32 bytes and
apply the lookup to the 32 chunks of `a`, `b`, and `c` to see if
`a[i] OP b[i] == c[i]` holds for `i = 0..32`, where `OP` belongs to
`[AND, OR, XOR]`.

## Constraints

1. opcodeId checks
   - opId == OpcodeId(0x16) for `AND`
   - opId == OpcodeId(0x17) for `OR`
   - opId == OpcodeId(0x18) for `XOR`
2. state transition:
   - gc + 3
   - stack_pointer + 1
   - pc + 1
   - gas + 3
3. Lookups: 35 busmapping lookups
   - `a` is at the top of the stack
   - `b` is at the second position of the stack
   - `c`, the result, is at the new top of the stack
   - Apply the lookup to 32 tuples of `a, b, c` chunks,
     `(a[i], b[i], c[i]), i = 0..32`, with opcode corresponding table
     (`BitwiseAnd`, `BitwiseOr`, and `BitwiseXor`).

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/opcode/bitwise.py`
