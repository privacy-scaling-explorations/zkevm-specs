# SHR opcode

## Procedure

The `SHR` opcode shifts the bits towards the least significant one. The bits moved before the first one are discarded, the new bits are set to 0.

### EVM behavior

Pop two EVM words `a` and `shift` from the stack, and push `b` to the stack, where `b` is computed as:

1. If `shift >= 256`，then `b` should be equal to zero.
2. If `shift < 256`，compute `b = a >> shift`.

### Circuit behavior

To prove the `SHR` opcode, we first construct a `ShlGadget` that proves `a >> shift = b` where `a, b, shift` are all 256-bit words.
As usual, we use 32 cells to represent word `a` and `b`, where each cell holds a 8-bit value. Then split each word into four 64-bit limbs denoted by `a[i]` and `b[i]` where i in `(0, 1, 2, 3)`.
We put the lower `n` bits of a part into the `lo` array, and put the higher `64 - n` bits of a part into the `hi` array. During the `SHR` operation, the `lo` array will move to higher bits of the result, and the `hi` array will move to lower bits of the result.

First we define the below variables:

* `shift_div_by_64 = shift // 64`
* `shift_mod_by_64 = shift % 64`
* `shift_mod_by_64_div_by_8 = shift % 64 // 8`
* `shift_mod_by_64_pow = 1 << shift_mod_by_64`
* `shift_mod_by_64_decpow = (1 << 64) // shift_mod_by_64_pow`
* `shift_mod_by_8 = shift % 8`
* `shift_overflow`: It equals to `0` if `shift[i] = 0` where i in (1, 2,..., 31), `1` otherwise.
* `a_slice_hi[i] = a[i] // (1 << shift_mod_by_64)`
* `a_slice_lo[i] = a[i] % (1 << shift_mod_by_64)`

Then we could compute the below variables:

* `a_slice_hi_digits[i]`:
```
a_slice_hi_digits[0] = \sum_{0}^{7} a_slice_hi[i] \cdot 2^{8 \cdot i}
a_slice_hi_digits[1] = \sum_{0}^{7} a_slice_hi[i + 8] \cdot 2^{8 \cdot i}
a_slice_hi_digits[2] = \sum_{0}^{7} a_slice_hi[i + 16] \cdot 2^{8 \cdot i}
a_slice_hi_digits[3] = \sum_{0}^{7} a_slice_hi[i + 24] \cdot 2^{8 \cdot i}
```
* `a_slice_lo_digits[i]`:
```
a_slice_lo_digits[0] = \sum_{0}^{7} a_slice_lo[i] \cdot 2^{8 \cdot i}
a_slice_lo_digits[1] = \sum_{0}^{7} a_slice_lo[i + 8] \cdot 2^{8 \cdot i}
a_slice_lo_digits[2] = \sum_{0}^{7} a_slice_lo[i + 16] \cdot 2^{8 \cdot i}
a_slice_lo_digits[3] = \sum_{0}^{7} a_slice_lo[i + 24] \cdot 2^{8 \cdot i}
```
* `b_digits[i]`:
```
b_digits[0] = \sum_{0}^{7} b[i] \cdot 2^{8 \cdot i}
b_digits[1] = \sum_{0}^{7} b[i + 8] \cdot 2^{8 \cdot i}
b_digits[2] = \sum_{0}^{7} b[i + 16] \cdot 2^{8 \cdot i}
b_digits[3] = \sum_{0}^{7} b[i + 24] \cdot 2^{8 \cdot i}
```

During `SHR`, assume that `a_slice_hi_digits[i]` move to the lower part of `b_digit[j]`, then `a_slice_lo_digits[i]` move to the higher part of `b_digit[j - 1]` (if `j == 0` then it will disappear apparently).

Then redefine the variables above:

* `x = shift_div_by_64`
* `y = shift_mod_by_64_div_by_8`
* `z = shift_mod_by_8`

TODO: Constraints
TODO: Lookup

## Constraints

1. opId = OpcodeId(0x1c)
2. state transition:
   - gc + 3 (2 stack reads + 1 stack write)
   - stack_pointer + 1
   - pc + 1
   - gas + 3
3. lookups: 3 busmapping lookups
   - `a` is at the top of the stack
   - `shift` is at the second position of the stack
   - `b`, the result, is at the new top of the stack

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/evm/execution/shr.py`
