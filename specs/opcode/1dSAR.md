# SAR opcode

## Procedure

The `SAR` opcode shifts the bits towards the least significant one. The bits moved before the first one are discarded, the new bits are set to 0 if the previous most significant bit was 0, otherwise the new bits are set to 1.

### EVM behavior

Pop two EVM words `shift` and `a` from the stack, and push `b` to the stack, where `b` is calculated as `b = a >> shift`.

Both `a` and `b` are considered as `signed` 256-bit values.

### Circuit behavior

To prove the `SAR` opcode, we first get the stack word `shift`, `a` and `b` to construct a gadget that proves `a >> shift == b`.

The `shift` is an `unsigned` value, but both `a` and `b` are `signed` values. A `signed` value is either negative or non-negative. The value is negative if the highest bit is 1, otherwise it is non-negative.

As usual, we use 32 cells to represent word `a` and `b`, where each cell holds an 8-bit value. Then split each word into four 64-bit limbs denoted by `a64s[idx]` and `b64s[idx]` where idx in `(0, 1, 2, 3)`.

We put the lower `n` bits of a limb into the `lo` array, and put the higher `64 - n` bits into the `hi` array, where `n = shift % 64`. During the right shift operation, the `lo` array will move to higher bits of the result, and the `hi` array will move to next lower bits.

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

Specially the top new bits are set to 1 if `a` is negative, otherwise set to 0.

More formally, the variables are defined as follows:
```
MAX_U64 = 2**64 - 1
is_neg = is_neg(a)
shf0 = bytes_to_fq(shift.le_bytes[:1])
shf_div64 = shift // 64
shf_mod64 = shift % 64
p_lo = 1 << shf_mod64
p_hi = 1 << (64 - shf_mod64)
# The new bits are set to 1 if negative.
p_top = is_neg * (MAX_U64 - p_hi + 1))
shf_lt256 = is_zero(sum(shift[1:]))
a64s = word_to_64s(a)
a64s_lo[idx] = a64s[idx] % p_lo
a64s_hi[idx] = a64s[idx] / p_lo
shf_div64_eq0 = is_zero(shf_div64)
shf_div64_eq1 = is_zero(shf_div64 - 1)
shf_div64_eq2 = is_zero(shf_div64 - 2)
shf_div64_eq3 = is_zero(shf_div64 - 3)
```

`b64s` could be calculated by these variables:

* Initialization: It should be `[MAX_U64] * 4` if `a` is negative, `[0] * 4` otherwise.
* `b64s[k]`: It could be calculated by `a64s_hi[k + shf_div64] + a64s_lo[k + shf_div64 + 1] * p_hi` where `k < 3 - shf_div64`.
* `b64s[3 - shf_div64]`: It could be calculated by `a64s_hi[3] + p_top`.

Now putting things together, the constraints can be constructed as follows:

1. `a64s` and `b64s` constraints:

* First calculate `shf_lt256` as `is_zero(sum(shift[1:]))`.
* `a64s[idx]`: It should be equal to `from_bytes(a[8 * idx : 8 * (idx + 1)])` where idx in `(0, 1, 2, 3)`.
* `b64s[idx] * shf_lt256 + is_neg * (1 - shf_lt256) * MAX_U64`: It should be equal to `from_bytes(b[8 * idx : 8 * (idx + 1)])` where idx in `(0, 1, 2, 3)`.

2. `a64s_lo` and `a64s_hi` constraints:

* `a64s[idx]`: It should be equal to `a64s_lo[idx] + a64s_hi[idx] * p_lo`.
* `a64s_lo[idx]`: It should always be less than `p_lo` (`a64s_lo[idx] < p_lo`).
* `a64s_hi[idx]`: It should always be less than `p_hi` (`a64s_hi[idx] < p_hi`).

3. Merge constraints:

* First create four `IsZero` gadgets:
```
shf_div64_eq0 = is_zero(shf_div64)
shf_div64_eq1 = is_zero(shf_div64 - 1)
shf_div64_eq2 = is_zero(shf_div64 - 2)
shf_div64_eq3 = is_zero(shf_div64 - 3)
```

* `b64s[0]` should be equal to:
```
(a64s_hi[0] + a64s_lo[1] * p_hi) * shf_div64_eq0 +
  (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq1 +
  (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq2 +
  (a64s_hi[3] + p_top) * shf_div64_eq3 +
  is_neg * MAX_U64 * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2 - shf_div64_eq3)
```

* `b64s[1]` should be equal to:
```
(a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq0 +
  (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq1 +
  (a64s_hi[3] + p_top) * shf_div64_eq2 +
  is_neg * MAX_U64 * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2)
```

* `b64s[2]` should be equal to:
```
(a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq0 +
  (a64s_hi[3] + p_top) * shf_div64_eq1 +
  is_neg * MAX_U64 * (1 - shf_div64_eq0 - shf_div64_eq1)
```

* `b64s[3]` should be equal to:
```
(a64s_hi[3] + p_top) * shf_div64_eq0 +
  is_neg * MAX_U64 * (1 - shf_div64_eq0)
```

4. `shift[0]` constraint:

* `shift[0]`: It should be equal to `shf_mod64 + shf_div64 * 64`.

5. `Pow2` table look up:

* First build `Pow2` table by tuple `(value, value_pow)` which meets `value_pow == pow(2, value)`.

* Look up for `p_lo == pow(2, shf_mod64)` and `p_hi == pow(2, 64 - shf_mod64)`.

6. Stack pop and push:

* Pop word `a`
* Pop word `shift`
* Push word `shift_lt256 * b + is_neg * (1 - shf_lt256) * ((1 << 256) - 1)`

## Constraints

1. opcodeId checks
   - opId === OpcodeId(0x1d) for `SAR`
2. state transition:
   - gc + 3 (2 stack reads + 1 stack write)
   - `stack_pointer` + 1
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

See `src/zkevm_specs/evm/execution/sar.py`
