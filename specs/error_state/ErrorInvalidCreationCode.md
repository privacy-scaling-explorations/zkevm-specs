# InvalidCreationCode state

## Procedure

InvalidCreationCode is an error related with code store. This error only occurs when executing CREATE or CREATE2 opcode or contract creation transaction (`tx.to == null`).

### EVM behavior

When handling a contract creation transaction, bytecodes to initialize are run and the current call context is CREATE. The last opcode to store for new contract is RETURN. It returns `memory[offset...offset + length]` content as bytecodes to store into state DB.

In bus-mapping, when the executing opcode is RETURN and the current call context is CREATE, check if the first byte of contract code is 0xEF to identify this error.

Even though this error occurs in CREATE or CREATE2, this error should be constrained in the RETURN opcode. Since it is easy to get the available memory length and construct constraints with it.

Overall it looks as the following:

- Pop EVM word `offset` and `length` from the stack.
- Go to InvalidCreationCode state when the current call context is CREATE and the first byte of contract code is 0xEF.

### Constraints

1. The first byte of contract code is 0xEF.
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`.
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups

- Byte code lookup.
- Stack reads for `offset` and `length`.
- Call context lookups for `is_success` and `rw_counter_end_of_reversion`.
- Restore context lookups for non-root call.

## Code

TODO: add after circuit merge first.
