# ErrorCodeStore state

## Procedure
`ErrorCodeStore` is for two original code store related errors: `CodeStoreOutOfGas` and 
`MaxCodeSizeExceeded`.
this type of error only occurs when executing create(create,create2) op code or tx deploy 
transaction(tx.to = null).

### EVM behavior
when in create kind transaction, init bytecodes will run and current call context is creating.
the final bytecodes to store for new contract is `RETURN` opcode of init codes result. `RETURN` opcode returns
memory [`offset`...`offset` + `length`] content as bytecodes to store into state db.
for returned bytecodes, store them cost additional gas.   

`let CODE_DEPOSIT_BYTE_COST = 200
code_store_cost = CODE_DEPOSIT_BYTE_COST * bytecodes' length
`  

if `code_store_cost` > gas left, it is `CodeStoreOutOfGas` case.  
if returned bytecodes' length > `MAXCODESIZE` allowed in evm, it is 
`MaxCodeSizeExceeded` case.  

in circuit buss mapping side, check these two code store errors in [https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/main/bus-mapping/src/circuit_input_builder/input_state_ref.rs#L1148&L1155]
when executing op code is `RETURN` and call context is creating(`call.is_create == true`) at the meanwhile.  

even though errors occur in `create` kind op codes, it is special not checking error 
in executing op code `create` directly.  
circuit implementation take similar strategy, not constrain error directly in create op codes, but 
in `RETURN` step context. following this way it easy to get the key property state `length` and construct constraint
against it.

overall as following:  
Pop EVM word `offset` and `length` from the stack, 
then go to `ErrorCodeStore` state when call context is creating & 
one of the followings occurs:

-  storing `length` of bytecodes out of gas
-  `length` of bytecodes exceeds `MAXCODESIZE`

### Constraints
1. `code_store_cost` > gas_left or `length` > `MAXCODESIZE`
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