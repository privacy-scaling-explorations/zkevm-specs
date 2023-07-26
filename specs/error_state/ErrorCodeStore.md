# ErrorCodeStore state

## Procedure
`ErrorCodeStore` is for two original code store related errors: `CodeStoreOutOfGas` and `MaxCodeSizeExceeded`. This type of error only occurs when executing create(create,create2) op code or tx deploy transaction(tx.to = null).

### EVM behavior
When handling a CREATE-kind transaction, Initial bytecode opcodes will run and current call context is created. The final bytecode opcodes to store for new contract is the `RETURN` opcode of init codes result.

`RETURN` opcode returns memory [`offset`...`offset` + `length`] content as bytecode to store into state db. For returned bytecode, store them cost additional gas.   

```
let CODE_DEPOSIT_BYTE_COST = 200
code_store_cost = CODE_DEPOSIT_BYTE_COST * len(bytecodes)
``` 

- If `code_store_cost` > gas left, it is `CodeStoreOutOfGas` case.
- If returned bytecode length > `MAXCODESIZE`, it is `MaxCodeSizeExceeded` case.  

In circuit bus mapping side, check these two code store errors in [here](https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/main/bus-mapping/src/circuit_input_builder/input_state_ref.rs#L1148&L1155). When executing opcode is `RETURN` and call context is creating(`call.is_create == true`) meanwhile.  

Even though errors occur in `CREATE` kind opcodes, it is special not checking error in executing opcode `CREATE` directly. Circuit implementation takes similar strategy, not constrain error directly in CREATE opcodes, but in `RETURN` step context. Following this way it easy to get the key property state `length` and construct constraints against it.

Overall it looks like the following:  
- Pop EVM word `offset` and `length` from the stack, 
- Go to `ErrorCodeStore` state when call context is being created & select which one of the followings occurs:
  1. Storing `length` of bytecode runs out of gas.
  2. `length` of bytecode exceeds `MAXCODESIZE`.

### Constraints
1. `code_store_cost` > gas_left or `length` > `MAXCODESIZE`
2. Current call must be failed.
3. Current call is not static call.
4. If it's a root call, it transits to `EndTx`
5. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- Byte code lookup.
- Stack reads for `offset` and `length`. 
- Call context lookups for `is_success` and `rw_counter_end_of_reversion`.
- Restore context lookups for non-root call.

## Code
   Please refer to `src/zkevm_specs/evm/execution/error_code_store.py`.