# SHR opcode

## Procedure

The `SHR` opcode shifts the bits towards the least significant one. The bits moved before the first one are discarded, the new bits are set to 0.

### EVM behavior

Pop two EVM words `a` and `shift` from the stack, and push `b` to the stack, where `b` is computed as:

1. If `shift >= 256`，then `b` is set to zero.
2. If `shift < 256`，compute `b = a >> shift`.

### Circuit behavior

To prove the `SHR` opcode, we first construct a `ShrGadget` that proves `a >> shift = b` where `a, b, shift` are all 256-bit words.
As usual, we use 32 cells to represent word `a` and `b`, where each cell holds a 8-bit value. Then split each word into four 64-bit limbs denoted by `a64s[idx]` and `b64s[idx]` where idx in `(0, 1, 2, 3)`.
We put the lower `n` bits of a limb into the `lo` array, and put the higher `64 - n` bits into the `hi` array, where `n` is `shift % 64`. During the SHR operation, the `lo` array will move to higher bits of the result, and the `hi` array will move to lower bits of the result.

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

More formally, the variables are defined as follows:

```
shf0 = bytes_to_fq(shift.le_bytes[:1])
shf_div64 = shift // 64
shf_mod64 = shift % 64
shf_lt256 = is_zero(sum(shift[1:]))
p_lo = 1 << shf_mod64
p_hi = 1 << (64 - shf_mod64)
a64s = word_to_64s(a)
a64s_lo[idx] = a64s[idx] % p_lo
a64s_hi[idx] = a64s[idx] / p_lo
```

If `shift >= 256`, `b64s` are all 0. Otherwise, `b64s` can be calculated by `a >> shf0` then split into four 64-bit limbs.

Now putting things together, the constraints can be constructed as follows:

1. `a64s` and `b64s` constraints:

* First calculate `shf_lt256` as `is_zero(sum(shift[1:]))`.
* `a64s[idx]`: It should be equal to `from_bytes(a[8 * idx : 8 * (idx + 1)])` where idx in `(0, 1, 2, 3)`.
* `b64s[idx] * shf_lt256`: It should be equal to `from_bytes(b[8 * idx : 8 * (idx + 1)])` where idx in `(0, 1, 2, 3)`.

2. `a64s_lo` and `a64s_hi` constraints:

* `a64s[idx]`: It should be equal to `a64s_lo[idx] + a64s_hi[idx] * p_lo`.
* `a64s_lo[idx]`: It should always be less than `p_lo` (`a64s_lo[idx] < p_lo`).

3. Merge constraints:

* First create three `IsZero` gadgets:
```
shf_div64_eq0 = is_zero(shf_div64)
shf_div64_eq1 = is_zero(shf_div64 - 1)
shf_div64_eq2 = is_zero(shf_div64 - 2)
```

* `b64s[0]` should be equal to:
```
(a64s_hi[0] + a64s_lo[1] * p_hi) * shf_div64_eq0 +
  (a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq1 +
  (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq2 +
  a64s_hi[3] * (1 - shf_div64_eq0 - shf_div64_eq1 - shf_div64_eq2)
```

* `b64s[1]` should be equal to:
```
(a64s_hi[1] + a64s_lo[2] * p_hi) * shf_div64_eq0 +
  (a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq1 +
  a64s_hi[3] * shf_div64_eq2
```

* `b64s[2]` should be equal to:
```
(a64s_hi[2] + a64s_lo[3] * p_hi) * shf_div64_eq0 +
  a64s_hi[3] * shf_div64_eq1
```

* `b64s[3]` should be equal to:
```
a64s_hi[3] * shf_div64_eq0
```

4. `shift[0]` constraint:

* `shift[0]`: It should be equal to `shf_mod64 + shf_div64 * 64`.

5. `Pow2` table look up:

* First build `Pow2` table by tuple $[value, value\_pow]$ which meets $${value\_pow == 2^{value}}$$

* Look up for `(shf_mod64, p_lo)` and `(64 - shf_mod64, p_hi)`

6. Stack pop and push:

* Pop word `a`
* Pop word `shift`
* Push word `shift_lt256 * b`

## Constraints

1. opId = OpcodeId(0x1c)
2. state transition:
   - gc + 3 (2 stack reads + 1 stack write)
   - stack\_pointer + 1
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
