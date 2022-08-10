# SHL and SHR opcodes

## Procedure

### EVM behavior

Pop two EVM words `shift` and `a` from the stack, and push `b` to the stack, where `b` is computed as

- for opcode SHL, `shift` is a number of bits to shift to the left, compute `b = (a * 2^shift) % 2^256` when `shift < 256` otherwise `b = 0`
- for opcode SHR, `shift` is a number of bits to shift to the right, compute `b = a // 2^shift` when `shift < 256` otherwise `b = 0`

### Circuit behavior

To prove the SHL and SHR opcodes, we first construct a `MulAddWordsGadget` that proves `quotient * divisor + remainder = dividend (% 2^256)` where quotient, divisor, remainder and dividend are all 256-bit words. Reference `02MUL_04DIV_06MOD.md` for details about `MulAddWordsGadget`.

Based on different opcode cases, we constrain the stack pops and pushes as follows

- for opcode SHL, two stack pops are shift and quotient, when `divisor = 2^shift` if `shift < 256` and 0 otherwise. The stack push is dividend if `shift < 256` and 0 otherwise.
- for opcode SHR, two stack pops are shift and dividend, when `divisor = 2^shift` if `shift < 256` and 0 otherwise. The stack push is quotient if `shift < 256` and 0 otherwise.

The opcode circuit also adds some extra constraints:

- contrain `shift == shift.cells[0]` when `divisor != 0`.
- use a `LtWordGadget` to constrain `remainder < divisor` when `divisor != 0`.
- if the opcode is SHL, constrain `remainder == 0`.
- if the opcode is SHR, constrain `overflow == 0` in `MulAddWordsGadget`.

## Constraints

1. opcodeId checks
   - opId === OpcodeId(0x1b) for SHL
   - opId === OpcodeId(0x1c) for SHR
2. state transition:
   - gc + 3
   - stack_pointer + 1
   - pc + 1
   - gas + 3
3. Lookups: 1 pow2 lookup + 3 busmapping lookups
   - divisor lookup in pow2 table (where 0≤shf0<256)  
      - when `shf0 < 128`, constrain `divisor_lo == 2^shf0`.
      - when `shf0 >= 128`, constrain `divisor_hi == 2^(shf0 - 128)`.
   - top of the stack
      - when opcode is SHL, quotient is at the top of the stack.
      - when opcode is SHR, dividend is at the top of the stack.
   - shift is at the second position of the stack when `divisor = 2^shift`.
   - new top of the stack
      - when opcode is SHL, dividend is at the new top of the stack.
      - when opcode is SHR, quotient is at the new top of the stack if `divisor != 0` otherwise 0.

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

See `src/zkevm_specs/evm/execution/shl_shr.py`
