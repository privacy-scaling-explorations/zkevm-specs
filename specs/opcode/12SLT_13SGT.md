# SLT & SGT opcode

## Procedure

The `SLT` and `SGT` opcodes compare the top two values on the stack, and push the result (0 or 1) back to the stack.

The stack inputs `a` and `b` are 256-bits signed integers with the most significant bit being the sign (1 for negative and 0 for positive). The 256-bits are in the two's complement form of representing signed integers.

#### Circuit Behaviour

The `SignedComparatorGadget` takes arguments `a: [u8; 32]`, `b: [u8; 32]` and `is_sgt: bool`.

It returns the result of `a < b` where:
- `Stack = [b, a]` if `is_sgt == false`
- `Stack = [a, b]` if `is_sgt == true`

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
2. Out of gas: gas left < 3

## Code

See [`src/zkevm_specs/opcode/slt_sgt.py`](../../src/zkevm_specs/evm/execution/slt_sgt.py)
