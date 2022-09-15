# EXP opcode

## EVM Behaviour

The `EXP` opcode performs an exponential operation. It reads the integer base `base` and integer exponent `exponent` from the top of the stack and pushes the exponentiation result, i.e. `base ^ exponent (mod 2^256)` to the top of the stack.

## Constraints

1. opId == 0x0A
2. State Transition:
    - rw_counter += 3
    - stack_pointer += 1
    - pc += 1
    - gas -= static_gas + dynamic_gas, where:
        - `static_gas = 10`
        - `dynamic_gas = 50 * byte_size(exponent)`
3. Lookups:
    - `base` is at the top of the stack (Read from RW Table)
    - `exponent` is at the second position of the stack (Read from RW Table)
    - `exponentiation` is at the top of the stack (Write to RW Table)
    - if `exponent == 2`:
        - Do a lookup to exponentiation table for
	```
	(
	    is_last=1,
	    base_limbs,
	    exponent_lo_hi,
	    exponentiation_lo_hi,
	)
	```
    - if `exponent > 2`:
        - Do a lookup to exponentiation table for:
	```
	(
	    is_last=0,
	    base_limbs,
	    exponent_lo_hi,
	    exponentiation_lo_hi,
	)
	```
	- Do a lookup to exponentiation table for:
	```
	(
	    is_last=1,
	    base_limbs,
	    exponent_lo_hi=[2, 0],
	    base_sq_lo_hi,
	)
	```
	where `base_sq_lo_hi` are the 128-bit low-high parts of `base * base (mod 2^256)`

## Exceptions

1. Stack underflow: The stack is empty or contains only one element.
2. Out of gas: The gas available is not sufficient to cover the cost of the exponentiation operation.

## Code

Please refer to [EXP gadget](../../src/zkevm_specs/evm/execution/exp.py)
