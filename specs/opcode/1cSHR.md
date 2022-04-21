# SHR opcode

## Procedure

The `SHR` opcode shifts the bits towards the least significant one. The bits moved before the first one are discarded, the new bits are set to 0.

### EVM behavior

Pop two EVM words `a` and `shift` from the stack, and push `b` to the stack, where `b` is computed as:

1. If `shift >= 256`，then `b` is set to zero.
2. If `shift < 256`，compute `b = a >> shift`.

### Circuit behavior

To prove the `SHR` opcode, we first construct a `ShlGadget` that proves `a >> shift = b` where `a, b, shift` are all 256-bit words.
As usual, we use 32 cells to represent word `a` and `b`, where each cell holds a 8-bit value. Then split each word into four 64-bit limbs denoted by `a[i]` and `b[i]` where i in (0, 1, 2, 3).
We put the lower `n` bits of a limb into the `lo` array, and put the higher `64 - n` bits into the `hi` array. During the SHR operation, the `lo` array will move to higher bits of the result, and the `hi` array will move to lower bits of the result.

#### Variable Definition

First we define the below variables:

* `shift_div_by_64 = shift // 64`
* `shift_mod_by_64 = shift % 64`
* `shift_mod_by_64_div_by_8 = shift % 64 // 8`
* `shift_mod_by_64_pow = 1 << shift_mod_by_64`
* `shift_mod_by_64_decpow = (1 << 64) // shift_mod_by_64_pow`
* `shift_mod_by_8 = shift % 8`
* `shift_overflow`: It is set to `0` if `shift[i] = 0` where i in (1, 2,..., 31), `1` otherwise.
* `a_slice_hi[i] = a[i] // (1 << shift_mod_by_64)`
* `a_slice_lo[i] = a[i] % (1 << shift_mod_by_64)`

Then we could compute the below variables:

* a_slice_hi_digits[i]:

$$
\cases{
    a\_slice\_hi\_digits_0 = \sum_{0}^{7} a\_slice\_hi_i \cdot 2^{8 \cdot i} \\
    a\_slice\_hi\_digits_1 = \sum_{0}^{7} a\_slice\_hi_{i+8} \cdot 2^{8 \cdot i} \\
    a\_slice\_hi\_digits_2 = \sum_{0}^{7} a\_slice\_hi_{i+16} \cdot 2^{8 \cdot i} \\
    a\_slice\_hi\_digits_3 = \sum_{0}^{7} a\_slice\_hi_{i+24} \cdot 2^{8 \cdot i} \\
}
$$

* a_slice_lo_digits[i]:

$$
\cases{
    a\_slice\_lo\_digits_0 = \sum_{0}^{7} a\_slice\_lo_i \cdot 2^{8 \cdot i} \\
    a\_slice\_lo\_digits_1 = \sum_{0}^{7} a\_slice\_lo_{i+8} \cdot 2^{8 \cdot i} \\
    a\_slice\_lo\_digits_2 = \sum_{0}^{7} a\_slice\_lo_{i+16} \cdot 2^{8 \cdot i} \\
    a\_slice\_lo\_digits_3 = \sum_{0}^{7} a\_slice\_lo_{i+24} \cdot 2^{8 \cdot i} \\
}
$$

* b_digits[i]:

$$
\cases{
    b\_digits_0 = \sum_{0}^{7} b_i \cdot 2^{8 \cdot i} \\
    b\_digits_1 = \sum_{0}^{7} b_{i+8} \cdot 2^{8 \cdot i} \\
    b\_digits_2 = \sum_{0}^{7} b_{i+16} \cdot 2^{8 \cdot i} \\
    b\_digits_3 = \sum_{0}^{7} b_{i+24} \cdot 2^{8 \cdot i} \\
}
$$

During SHR, assume that `a_slice_hi_digits[i]` move to the lower part of `b_digit[j]`, then `a_slice_lo_digits[i]` move to the higher part of `b_digit[j - 1]` (if `j == 0` then it will disappear apparently).

And redefine the variables above:

* `x = shift_div_by_64`
* `y = shift_mod_by_64_div_by_8`
* `z = shift_mod_by_8`

#### Constraint Validation

Then we could validate the below constraints:

1. SHR main constraints:

* Assume i in (0, 1,...,3 - x - 1), j in (3 - x + 1,...,3).
* `b_digits[i]`: It should equal to `a_slice_hi_digits[i + x] + alice_lo_digits[i + x + 1] * shift_mod_by_64_decpow` if `shift_overflow == 0`, otherwise it should be zero if `shift_overflow == 1`.
* `b_digits[3 - x]`: It should equal to `a_slice_hi_digits[3]` if `shift_overflow == 0`, otherwise it should be zero if `shift_overflow == 1`.
* `b_digits[j] = 0`.

2. shift[0] spilit constraints:

* `shift[0]`: It should equal to `x * 64 + y * 8 + z` if `shift_overflow == 0`.

3. shift range constraints:

* `shift[i]`: It should equal to zero where i in (1, 2,...,31) if `shift_overflow == 0`.

4. merge contraints:

* `a_digits[i]`: It should equal to `a_slice_lo_digits[i] + a_slice_hi_digits[i] * shift_mod_by_64_pow` where i in (0, 1, 2, 3).

5. slice higher cell equal to zero constraints:

* `a_slice_lo[i]`: It should equal to zero if `i % 64 >= y + 1`.
* `a_slice_hi[i]`: It should equal to zero if `i % 64 >= 8 - y`.

Specifically we can add up all cells and validate it equals to zero. Because all cells are in range [0, 255].

#### Lookup Validation

We also add two new lookup tables used for validation.

1. Bitslevel table

The table is formed by triple $[idx,val,0]$, which meets $$val\stackrel{?}{\in}[0,2^{idx})$$
It is used for range check whose upper bound is equals to pow of two.
During SHR, this table checks the last cell of each part of `a_slice_hi` and `a_slice_lo`.
For `a_slice_hi`, the last cell should only have `8 - shift_mod_by_8` bits.
For `a_slice_lo`, the last cell should only have `shift_mod_by_8` bits.

$$
\begin{aligned}
\cases{
a\_slice\_lo[x] \stackrel{?}{\in} [0,2^z)\\\\
a\_slice\_lo[8+x] \stackrel{?}{\in} [0,2^z)\\\\
a\_slice\_lo[16+x] \stackrel{?}{\in} [0,2^z)\\\\
a\_slice\_lo[24+x] \stackrel{?}{\in} [0,2^z)\\\\
}
\end{aligned}
$$
$$
\begin{aligned}
\cases{
a\_slice\_hi[7-x] \stackrel{?}{\in} [0,2^{8-z})\\\\
a\_slice\_hi[15-x] \stackrel{?}{\in} [0,2^{8-z})\\\\
a\_slice\_hi[23-x] \stackrel{?}{\in} [0,2^{8-z})\\\\
a\_slice\_hi[31-x] \stackrel{?}{\in} [0,2^{8-z})\\\\
}
\end{aligned}
$$
Meanwhile，we also need check the range of $x,y,z$.
$$
\begin{aligned}
\cases{
x\stackrel{?}{\in}[0,4)\\
y\stackrel{?}{\in}[0,8)\\
z\stackrel{?}{\in}[0,8)
}
\end{aligned}
$$

2. Pow64 table

The table is formed by triple $[idx,pow,decpow]$ ，which meets $$\begin{aligned}\cases{pow == 2^{idx}\\decpow == 2^{64-idx}}\end{aligned}$$

And during $SHR$ we need to check the triple $[x,shift\_mod\_by\_64\_pow,shift\_mod\_by\_64\_decpow]$.

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
