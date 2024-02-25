# JUMPI opcode

## Procedure

JUMPI is an op code regarding flow control of evm. it pops two values at the top of the stack and conditionally changes program counter .

### EVM behavior

Pop two EVM words `dest` and `cond` from the stack. then do the following:

1. check `cond` is zero

- set pc = pc + 1

2. check `cond` is not zero

- check `dest` is within code length range
- check `dest` is a JUMPDEST
- check `dest` is not data section of PUSH\*
- set pc = `dest`

### Circuit behavior

1. Construct byte code table with tuple of (code_hash, index, bytecode, is_code) in each row, the table validity will be ensured by another byte code circuit.
2. basic constraints:

- opId === OpcodeId(0x57)
- gc + 2 (2 stack read)
- pc = pc + 1 if `cond` is zero else `dest`
- stack_pointer + 2
- gas + 10

3. Lookups:

- lookup `dest` and `cond` are the top two of the stack
- Conditional lookup `dest` position is `JUMPDEST` code in byte code table
  when `cond` is not zero

## Exceptions

1. stack underflow:   when stack is empty ` stack_pointer in [1023,1024]`
2. out of gas: remaining gas is not enough
3. invalid jump (AKA ErrInvalidJump):\
   the `dest` is not JUMPDEST or not code or out of range

## Code

Refer to src/zkevm_specs/evm/execution/jumpi.py
