# NOT opcode

## Procedure

Pop one EVM word `a` from the stack and push output `b` onto the stack.

We prove that `a = NOT b` by showing that the byte-wise relation
`a[i] XOR b[i] == 255` holds for each of `i = 0..32`.

## Constraints

1. opcodeId checks
   - opId == OpcodeId(0x19)
2. state transition:
   - gc + 2
   - stack_pointer unchanged
   - pc + 1
   - gas + 3
3. Lookups: 34 busmapping lookups
   - `a` is at the top of the stack
   - `b`, the result, is at the new top of the stack
   - Apply the lookup to 32 tuples of `a, b` chunks, `(a[i], b[i]), i = 0..32`.

## Exceptions

1. stack underflow: `stack_pointer = 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/evm/execution/bitwise.py`
