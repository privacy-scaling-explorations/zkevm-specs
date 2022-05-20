# MULMOD opcode

## Procedure

### EVM behavior


Pop 3 EVM words `a`, `b` and `N` from the stack.

If `N` is 0:
	push 0 into the stack.
else:
	compute `r= (a * b) mod N` and push `r` into the stack.

*Note*
All intermediate calculations of this operation are not subject to the 2^256 modulo.

### Circuit behavior

The MulModGadget takes arguments:
 - `a: [u8;32]`
 - `b: [u8;32]`,
 - `N: [u8;32]`,
and keeps a cell for storing `minus_d: [u8;32]`.

- Check the equality ` a * b + minus_d * N  == r` (1)
TODO: Check this
```
	AddWordsGadget[
		[ MulWordsGadget[a, b],
		  MulWordsGadget[minus_d, N] ],
		r,
	]
```

- Check `r<n` (2)

To handle the case of `n==0` => `r==0`, if `N` is 0:

- witness `r <= a + b` to satisfy (1)
- deactivate (2)


## Constraints

1. opcodeID checks
   opId == OpcodeId(0x09)
2. state transition:
   - gc + 4
   - stack_pointer +2
   - pc + 1
   - gas + 8
3. Lookups: 4 busmapping lookups
   - `a` is on top of the stack.
   - `b` is in the second position of the stack.
   - `N` is in the third position of the stack.
   - `r`, the result is on top of the new stack.


## Exceptions

1. stack undeflow: `1022 <= stack_pointer <= 1024`.
2. out of gas: Remaining gas is not enough.

See `src/zkevm_specs/opcode/mulmod.py`
