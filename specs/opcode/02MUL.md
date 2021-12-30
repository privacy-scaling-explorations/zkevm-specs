# MUL op code

## Procedure

We followed the approch of [Multi-Limbs Multiplication](https://hackmd.io/HL0QhGUeQoSgIBt2el6fHA), with some notes:

In notation *c = a ⋅ b*, layout could be like the below table if we got 32 columns to use. In table, *a₀, ⋯, a₃₁* as well as *b* and *c* are evm words on stack through bus mapping lookup. Each limb in evm word will be range lookup check to fit 8-bit.

| 0  |  1 |  2 | 3  |  4 |  5 | ⋯  | 8  | ⋯ | 29 | 30 | 31 |
|----|----|----|----|----|----|----|----|----|----|----|----|
|*a₀*|*a₁*|*a₂*|*a₃*|*a₄*|*a₅*| ⋯  |*a₈*| ⋯ |*a₂₉*|*a₃₀*|*a₃₁*|
|*b₀*|*b₁*|*b₂*|*b₃*|*b₄*|*b₅*| ⋯  |*a₈*| ⋯ |*b₂₉*|*b₃₀*|*b₃₁*|
|*c₀*|*c₁*|*c₂*|*c₃*|*c₄*|*c₅*| ⋯  |*a₈*| ⋯ |*c₂₉*|*c₃₀*|*c₃₁*|
|*v0₀*|*v0₁*|*v0₂*|*v0₃*|*v0₄*|*v0₅*| ⋯  |*v0₈*|  | | | |
|*v1₀*|*v1₁*|*v1₂*|*v1₃*|*v1₄*|*v1₅*| ⋯  |*v1₈*|  | | | |

Linear combinations of *A, B and C* form 4 - 64 bit limbs for *a, b and c* respectively and no need to be stored as witness:

|                    |                     |                    |
|--------------------|---------------------|--------------------|
|*A₀ = Σ₀⁷aᵢ ⋅ 256ⁱ* | *B₀ = Σ₀⁷bᵢ ⋅ 256ⁱ* | *C₀ = Σ₀⁷cᵢ ⋅ 256ⁱ* |
|*A₁ = Σ₀⁷aᵢ₊₈ ⋅ 256ⁱ*|*B₁ = Σ₀⁷bᵢ₊₈ ⋅ 256ⁱ*|*C₁ = Σ₀⁷cᵢ₊₈ ⋅ 256ⁱ*|
|*A₂ = Σ₀⁷aᵢ₊₁₆ ⋅ 256ⁱ*|*B₂ = Σ₀⁷bᵢ₊₁₆ ⋅ 256ⁱ*|*C₂ = Σ₀⁷cᵢ₊₁₆ ⋅ 256ⁱ*|
|*A₃ = Σ₀⁷aᵢ₊₂₄ ⋅ 256ⁱ*|*B₃ = Σ₀⁷bᵢ₊₂₄ ⋅ 256ⁱ*|*C₃ = Σ₀⁷cᵢ₊₂₄ ⋅ 256ⁱ*|

> Note 1: we can in additional combine *A₀, A₁, B₀ ⋯* to *t₀, t₁ ⋯* for they are still some polynomial with rather low degree, and not need to store them as witness:

*t₀ = A₀B₀*

*t₁ = A₀B₁ + A₁B₀*

*t₂ = A₀B₂ + A₁B₁ + A₂B₀*

*t₃ = A₀B₃ + A₁B₂ + A₂B₁ + A₃B₀*

And the constraints would be:

- *v0 ⋅ 2¹²⁸ == t₀ + t₁ ⋅ 2⁶⁴ - C₀ - C₁ ⋅ 2⁶⁴*
- *v1 ⋅ 2¹²⁸ == v0 + t₂ + t₃ ⋅ 2⁶⁴ - C₂ - C₃ ⋅ 2⁶⁴*
- *v0 ∈ \[ 0, 2⁶⁶ \]*
- *v1 ∈ \[ 0, 2⁶⁶ \]*

> Note 2: we consider there should be a trivial mistake in the original link which claimed the range of v0 and v1 is `[0, 2^64]` (they should be in the range of `[0, 2^66]`).

> Note 3: Ensuring v0 and v1 do not exceed the scalar field after being mutipled by 2^128 is enough. In our code v0 and v1 are constrainted by the combination of 9 bytes (each cell being constrainted by 8-bit range table) so they are constrainted to a slightly relaxed range of `[0, 2^72)`. Our approach use 3 evm words and 18 cells (totally 114 cells).

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
