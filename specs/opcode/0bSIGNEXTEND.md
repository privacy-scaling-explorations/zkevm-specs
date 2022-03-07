# SIGNEXTEND opcode

## Procedure

The `SIGNEXTEND` opcode extends the length of a signed integer. This is done by popping two values, first the `index` and then the `value`, from the stack. The byte at position `index`, with the position starting at `0` at the LSB in `value`, will be used to read the sign from (with the sign being the most significant bit). All bytes following the selected byte (`> index`) will be replaced by a value depending on this sign:

- Sign is `0`: all bytes `> index` will be replaced with `0x00`
- Sign is `1`: all bytes `> index` will be replaced with `0xFF`

`result` is then pushed on the stack. If `index >= 31` no bytes will change and `result == value`.

## Constraints

1. opId = OpcodeId(0x0b)
2. state transition:
   - gc + 3 (2 stack reads + 1 stack write)
   - stack_pointer + 1
   - pc + 1
   - gas + 5
3. lookups: 1 fixed lookup + 3 busmapping lookups
   - The sign from the selected byte
   - `index` is at the top of the stack
   - `value` is at the new top of the stack
   - `result` is at the new top of the stack

## Exceptions

1. stack underflow: the stack is empty or only contains a single value
2. out of gas: the remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/opcode/signextend.py`.
