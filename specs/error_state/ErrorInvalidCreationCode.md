# ErrorInvalidCreationCode state

## Procedure

InvalidCreationCode is an error related with code store. This error only occurs when executing `CREATE` or `CREATE2` opcode or contract creation transaction (`tx.to == null`).

### EVM behavior

When handling either a `CREATE` or a`CREATE2` opcode, the initial bytecode is executed and the current call context is created. The contract bytecode will then be returned through the `RETURN` opcode as the execution result. More particularly, the contract bytecode will be defined as the memory chunk of length `length` starting at offset `offset`, that is the memory located at [`offset`...`offset` + `length`] is stored in the state db.


In bus-mapping, when the executing opcode is `RETURN` and the current call context is `CREATE` or `CREATE2`, check if the first byte of contract code is `0xEF` to identify this error.

Even though this error occurs in `CREATE` or `CREATE2`, this error should be constrained in the `RETURN` opcode. Since it is easy to get the available memory offset and construct constraints with it.

Overall it looks as the following:

- Pop EVM word `offset` from the stack.
- Go to `ErrorInvalidCreationCode` state when the current call context is `CREATE` or `CREATE2` and the first byte of the deployed bytecode is `0xEF`.

### Constraints

1. Current opcode is `RETURN` and `is_create` is True.
2. The first byte of contract code is `0xEF`.
3. Current call must be failed.
4. If it's a root call, it transits to `EndTx`.
5. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups

- Memory lookup.
- Stack reads for `offset`.
- Call context lookups for `is_success` and `rw_counter_end_of_reversion`.
- Restore context lookups for non-root call.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_invalid_creation_code.py`.