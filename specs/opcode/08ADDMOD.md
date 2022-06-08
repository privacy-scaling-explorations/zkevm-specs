# ADDMOD opcode

## Procedure

### EVM behavior

Pop three EVM words `a`, `b` and `N` from the stack.

If n is zero
	push 0 into the stack
else
	compute `r = (a + b) mod N`, and push `r` into to the stack

### Circuit behavior

The AddModGadget takes argument of `a: [u8;32]`, `b: [u8;32]`, `N: [u8;32]` and keeps a cell for storing `d :[u8;32]`

- Witness `(a_reduced,k) ← (a % N, a // N)` 
- Witness `(r,d) ← ( (a_reduced + b) % N, (a_reduced + b ) // N)`
- Check `a == a_reduced + k * N` (a_reduced + k * N should not overflow 256 bits)  
- Check `a_reduced + b == d * N + r` in 512bit space (1)  
- Check `r<N` (2)
- Check `a_reduced<N` (2)

To handle the case of `N==0` => `r==0`, if n is zero

- witness `r ← (a_reduced + b) % 2^256` to satisfy &1 
- deactivate &2

## Constraints

1. opcodeId checks
   opId === OpcodeId(0x08)
2. state transition:
   - gc + 4
   - stack_pointer + 2
   - pc + 1
   - gas + 8
3. Lookups: 4 busmapping lookups
   - `a` is at the top of the stack
   - `b` is at the second position of the stack
   - `n` is at the third position of the stack
   - `r`, the result, is at the new top of the stack

## Exceptions

1. stack underflow: `1022 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/opcode/addmod.py`
