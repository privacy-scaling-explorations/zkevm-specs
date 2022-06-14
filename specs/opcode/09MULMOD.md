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
 - `r: [u8;32]`,
 - `N: [u8;32]`,
and keeps 5 words for storing:
 - `a_reduced: [u8;32]` ,
 - `k: [u8;32]`,
 - `e: [u8;32]`,
 - `d: [u8;32]`
 - `zero: [u8;32]`.


 Witness `a_reduced ←  a` if `n!=0` else `a_reduced ← 0`
 Witness `(e, d) ← ( (a_reduced * b) % 2^256, (a_reduced * b ) // 2^256)`
 Witness `(r, k) ← ( (a_reduced * b) % N, (a_reduced * b ) // N)`

 1. Check `a_reduced = a mod N`.
	which uses `ModGadget` that in turn checks:
	- Check the equality ` j * N + a_reduced  == a `
	- Check (`a_reduced = 0` and `N == 0`) or `a_reduced < N`

 2. Check `r = a * b mod N`
	which uses 2 `MulAddWords512Gadget` to check:
	` a_reduced * b = k * N + r`  in 2 steps
		- `a_reduced * b + zero == d * 2^256 + e`
		- `k * N + r == d * 2^256 + e`

	1 `IsZeroGadget` and 1 `LtWordsGadget` that check:
	`(r == 0 and N == 0)` or `(r < N)`


#### Note

The first step on the computation, reducing `a` mod `N`, is taken in order
to prevent overflow in the factor `k`, which could happen for high values
of `a` and `b` and low `N`. This steps ensures:

$$
k \leq \frac{(a \text{ mod } n) \cdot b }{n } \leq \frac{ (n-1) \cdot b}{n} < b \leq MAXU256
$$

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
