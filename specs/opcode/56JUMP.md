# JUMP opcode

## Procedure

JUMP is an op code regarding flow control of evm. it takes the value of top stack
to use as the destination, which changes program counter to it.

### EVM behavior

Pop one EVM word `dest` from the stack. then do the followings:

- check `dest` is within code length range
- check `dest` is a `JUMPDEST` and not data section of PUSH\*
- set program counter = `dest`

### Circuit behavior

1. construct byte code table with tuple (code_hash, index, bytecode, is_code) in each row, the table validity will be ensured by another byte code circuit.
2. basic constraints:

- opId == OpcodeId(0x56)
- gc + 1 (1 stack read)
- pc = `dest`
- stack_pointer + 1
- gas + 8

3. Lookups:  1 busmapping lookups + 1 byte code lookup

- lookup `dest` at the top of the stack
- lookup `dest` position is `JUMPDEST` code in byte code table

## Exceptions

1. stack underflow:   when stack is empty `stack_pointer = 1024`
2. out of gas: remaining gas is not enough
3. invalid jump (AKA ErrInvalidJump):\
   the `dest` is not `JUMPDEST` or not code or out of range

## Code

refer to src/zkevm_specs/evm/execution/jump.py
