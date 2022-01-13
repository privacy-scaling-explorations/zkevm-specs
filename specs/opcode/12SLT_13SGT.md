# SLT & SGT opcode

## Procedure

The `SLT` and `SGT` opcodes compare the top two values on the stack, and push the result (0 or 1) back to the stack.

The stack inputs `a` and `b` are 256-bits signed integers with the most significant bit being the sign (1 for negative and 0 for positive). The 256-bits are in the two's complement form of representing signed integers.

#### Circuit Behaviour

The `SignedComparatorGadget` takes arguments `a: [u8; 32]`, `b: [u8; 32]` and `is_sgt: bool`.

It returns the result of `a < b` where:

- `Stack = [b, a]` if `is_sgt == false`
- `Stack = [a, b]` if `is_sgt == true`

We basically swap the stack inputs if `is_sgt == true`, so that we only need to compare `a < b` in our gadget.

The gadget is constructed with the following logic:

```python
# a < 0 and b >= 0
if a[31] >= 128 and b[31] < 128:
	result = 1
# b < 0 and a >= 0
elif b[31] >= 128 and a[31] < 128:
	result = 0
# (a < 0 and b < 0) or (a >= 0 and b >= 0)
else:
	if a_hi < b_hi:
		result = 1
	elif a_hi == b_hi and a_lo < b_lo:
		result = 1
	else:
		result = 0
```

where:

- `a[31]` and `b[31]` represent the most significant bytes of `a` and `b` respectively.
- `a[31] >= 128` (same for `b`) signifies that `a` (same for `b`) is a negative number.
- `a_hi = a[16..32]` and `a_lo = a[0..16]` (same for `b`) with `a` (same for `b`) being represented in the little-endian form.

## Constraints

- `OpcodeId` check:
  - opId === OpcodeId(0x12) for `SLT`
  - opId === OpcodeId(0x13) for `SGT`
- State Transition:
  - gc -> gc + 3
  - stack pointer -> stack pointer + 1
  - pc -> pc + 1
  - gas -> gas + 3
- Lookups:
  - `a` is at the top of the stack
  - `b` is at the second position of the stack
  - `result` is the new top of the stack

## Exceptions

1. Stack underflow: `1023 <= stack pointer <= 1024`
2. Out of gas: gas left \< 3

## Code

See [`slt_sgt.py`](../../src/zkevm_specs/evm/execution/slt_sgt.py)
