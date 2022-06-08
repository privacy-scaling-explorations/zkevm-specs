# SDIV and SMOD opcodes

## Procedure

### EVM behavior

Pop two EVM words `a` and `b` from the stack, and push `c` to the stack. All `a`, `b` and `c` are considered as `signed` values, and `a_abs`, `b_abs` and `c_abs` are absolute values of `a`, `b` and `c`.

- For opcode `SDIV`
  - `c = 0` when `b == 0`.
  - `c = -(1 << 255)` when `a == -(1 << 255)` and `b == -1`.
  - For other cases, compute `c_abs = a_abs // b_abs`,  and `sign(c) = sign(a // b)`.
- For opcode `SMOD`
  - `c = 0` when `b == 0`.
  - For other cases, compute `c_abs = a_abs % b_abs` and `sign(c) = sign(a)`.

### Circuit behavior

To prove the `SDIV/SMOD` opcode, we first get the stack word `pop1`, `pop2` and `push`, and get the absolute value `pop1_abs`, `pop2_abs` and `push_abs`.
Then use these values to calculate `quotient`, `divisor`, `remainder` and `dividend` for opcode `SDIV` and `SMOD` respectively. And get the absolute value `quotient_abs`, `divisor_abs`, `remainder_abs` and `dividend_abs`.
Then use these four absolute values to construct a `MulAddWordsGadget` (as described in `02MUL_04DIV_06MOD.md`). The constraints should be matched in `MulAddWordsGadget` since we use the absolute values of `quotient`, `divisor`, `remainder` and `dividend`.

Now putting things together, the constraints can be constructed as follows:

1. `MulAddWordsGadget` overflow:

* It should always be zero.

2. `divisor` and `remainder` absolute values:

* Constrain `abs(remainder) < abs(divisor)` when divisor != 0.

3. `dividend` and `remainder` signs:

* Constrain `sign(dividend) == sign(remainder)` when quotient, divisor and remainder are all non-zero.

4. `dividend`, `divisor` and `quotient` signs:

* `dividend_is_signed_overflow` is calculated for a special `SDIV` case, when input `dividend = -(1 << 255)` and `divisor = -1`, the quotient result should be `1 << 255`, which is overflow for a `signed` word. Since it could only express `signed` value from `-(1 << 255)` to `(1 << 255) - 1`.

* Constrain `sign(dividend) == sign(divisor) ^ sign(quotient)` when both quotient and divisor are non-zero and dividend is not signed overflow.

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x05) for `SDIV`
   2. opId === OpcodeId(0x07) for `SMOD`
2. state transition:
   - gc + 3 (2 stack reads + 1 stack write)
   - `stack_pointer` + 1
   - pc + 1
   - gas + 5
3. Lookups: 3 busmapping lookups
   - `dividend` is at the top of the stack.
   - `divisor` is at the second position of the stack.
   - new top of the stack
      - when it's `SDIV`, `quotient` is at the new top of the stack when `divisor != 0`, otherwise 0.
      - when it's `SMOD`, `remainder` is at the new top of the stack when `divisor != 0`, otherwise 0.

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/evm/execution/sdiv_smod.py`
