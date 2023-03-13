# InvalidCreationCode state

## Procedure
`InvalidCreationCode` is also code store related errors.  
this type of error only occurs when executing create(create,create2) op code or tx deploy 
transaction(tx.to = null).

### EVM behavior
When handling a CREATE-kind transaction, Initial bytecode opcodes will run and current call context is created.
The final bytecode opcodes to store for new contract is the `RETURN` opcode of init codes result.

`RETURN` opcode returns memory [`offset`...`offset` + `length`] content as bytecodes to store into state db.


In circuit bus mapping side, check these two code store errors in [here](https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/main/bus-mapping/src/circuit_input_builder/input_state_ref.rs#L1148&L1155)
when executing opcode is `RETURN` and call context is creating(`call.is_create == true`) meanwhile.  

Even though errors occur in `CREATE` kind opcodes, it is special not checking error 
in executing opcode `CREATE` directly.  
Circuit implementation takes similar strategy, not constrain error directly in CREATE opcodes, but 
in `RETURN` step context. Following this way it easy to get the key property state `length` and construct constraints against it.

Overall it looks like the following:  
- Pop EVM word `offset` and `length` from the stack, 
- Go to `InvalidCreationCode` state when call context is being created and first byte of code is 0xef.


### Constraints
1. first byte code is `0xef`
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- Byte code lookup.
- stack reads for `offset` and `length`. 
- call context lookups for `is_success` and `rw_counter_end_of_reversion`.
- Restore context lookups for non-root call.

## Code
    TODO: add after circuit merge first.