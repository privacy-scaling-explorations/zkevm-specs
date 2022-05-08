# SHR opcode

## Procedure

The `SHR` opcode shifts the bits towards the least significant one. The bits moved before the first one are discarded, the new bits are set to 0.

### EVM behavior

Pop two EVM words `a` and `shift` from the stack, and push `b` to the stack, where `b` is computed as:

1. If `shift >= 256`，then `b` is set to zero.
2. If `shift < 256`，compute `b = a >> shift`.

### Circuit behavior

To prove the `SHR` opcode, we first construct a `ShrGadget` that proves `a >> shift = b` where `a, b, shift` are all 256-bit words.
As usual, we use 32 cells to represent word `a` and `b`, where each cell holds a 8-bit value. Then split each word into four 64-bit limbs denoted by `a64s[idx]` and `b64s[idx]` where idx in (0, 1, 2, 3).
We put the lower `n` bits of a limb into the `lo` array, and put the higher `64 - n` bits into the `hi` array. During the SHR operation, the `lo` array will move to higher bits of the result, and the `hi` array will move to lower bits of the result.

The following figure illustrates how shift right works under the case of `shift < 64`.

```
+-------------------------------+-------------------------------+-----
|a0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10| 11| 12| 13| 14| 15| ...
+-------------------------------+-------------------------------+-----
|             a64s[0]           |             a64s[1]           | ...
+------------+------------------+------------+------------------+-----
| a64s_lo[0] |    a64s_hi[0]    | a64s_lo[1] |    a64s_hi[1]    | ...
+------------+------------------+------------+------------------+-----
             |            b64s[0]            |            b64s[1]
             +-------------------------------+------------------------
```

#### Variable Definition

More formally, the variables are defined as follows:

$$
\begin{align}
shf\_div64 &= shift // 64\\
shf\_mod64 &= shift \% 64\\
shf\_lt256 &= is\_zero(sum(shift[1:]))\\
p\_lo &= 2^{shf\_mod64} \\
p\_hi &= 2^{64 - shf\_mod64} \\
a64s[idx] &= \sum_{i=0}^7 a[8\cdot idx + i] \cdot 256^i~~~~(idx=0,1,2,3)\\
a64s\_lo[idx] &= a64s[idx] ~\%~p\_lo \\
a64s\_hi[idx] &= a64s[idx] ~/~ p\_lo \\
\end{align}
$$

If $shift\ge 256$, `b64s` are all 0. Otherwise, `b64s` can be derived using

$$
b64s[k] = \cases{
    a64s\_hi[k + shf\_div64] + a64s\_lo[k + shf\_div64 + 1] \cdot p\_hi & k < 3 - shf_div64 \\
    a64s\_hi[3] & k = 3 - shf_div64 \\
    0 & k > 3 - shf_div64
}
$$

#### Constraint Validation

Then we could validate the below constraints:

- `a64s[idx] == from_bytes(a[8 * idx : 8 * (idx + 1)])`
- `b64s[idx] == from_bytes(b[8 * idx : 8 * (idx + 1)])`
- `a64s[idx] == a64s_lo[idx] + a64s_hi[idx] * p_lo`
- `a64s_lo[idx] < p_lo`
- Create IsZero gadgets
    - `shf_div64_eq0 = is_zero(shf_div64)`
    - `shf_div64_eq1 = is_zero(shf_div64 - 1)`
    - `shf_div64_eq2 = is_zero(shf_div64 - 2)`
- `b64s[0] == (a64s_hi[0] + a64s_lo[1] * p_hi) * shf_div64_eq0 +`
  `(a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq1 +`
  `(a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq2 +`
  `a64s_hi[3] * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2)`
- `b64s[1] == (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq0 +`
  `(a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq1 +`
  `a64s_hi[3] * shf_div64_eq2`
- `b64s[2] == (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq0 +`
  `a64s_hi[3] * shf_div64_eq1`
- `b64s[3] == a64s_hi[3] * shf_div64_eq0`
- `shift[0] == shf_mod64 + shf_div64 * 64`
- Range check `shf_mod64` in the range [0, 64)
- Range check `shf_div64` in the range [0, 4)
- Look up Pow65 (since `shf_mod64` may be zero) table for `(shf_mod64, p_lo)` and `(64 - shf_mod64, p_hi)`
- `stack_pop(rlc_encode(a))`
- `stack_pop(rlc_encode(shift))`
- `stack_push(shift_lt256 * rlc_encode(b))`

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
