# ErrorCodeStore state

## Procedure
`ErrorCodeStore` is a combined error code for handling the `CodeStoreOutOfGas` and `MaxCodeSizeExceeded` code store related errors. This type of error only occurs when executing `CREATE`/`CREATE2` opcode or a deployment transaction (tx.to = null).

### EVM behavior
When handling either a `CREATE` or a`CREATE2` opcode, the initial bytecode is executed and the current call context is created. The contract bytecode will then be returned through the `RETURN` opcode as the execution result. More particularly, the contract bytecode will be defined as the memory chunk of length `length` starting at offset `offset`, that is the memory located at [`offset`...`offset` + `length`] is stored in the state db. The gas cost for storing the bytecode is:

```
let CODE_DEPOSIT_BYTE_COST = 200
code_store_cost = CODE_DEPOSIT_BYTE_COST * len(bytecodes)
``` 

Which error are we handling?
- If `code_store_cost` > gas left, `ErrorCodeStore` corresponds to `CodeStoreOutOfGas`;
- If returned bytecode length > `MAXCODESIZE`, it corresponds to `MaxCodeSizeExceeded`.

On the circuit bus mapping side, the checks for these two code store errors are [here](https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/8a633f7c3de2da72f0817def57c1703241cced97/bus-mapping/src/circuit_input_builder/input_state_ref.rs#L1296-L1304). This error only happens when both the current opcode is `RETURN` and the call is either `CREATE` or `CREATE2` call, that is when `call.is_create == true`. 

Even though these are `CREATE`/`CREATE2` errors, as we cannot get the contract bytecode length when processing these opcodes, we handle them in the `RETURN` opcode where the bytecode length is available.

Overall it looks like the following:  
- Pop EVM word `offset` and `length` from the stack, 
- Go to `ErrorCodeStore` state when call context is being created & select which one of the followings occurs:
  1. Storing `length` of bytecode runs out of gas.
  2. `length` of bytecode exceeds `MAXCODESIZE`.

### Constraints
1. Current opcode is `RETURN` and `is_create` is `True`.
2. `code_store_cost` > gas_left or `length` > `MAXCODESIZE`
3. Current call fails.
4. Current call is not static call.
5. If it's a root call, it transits to `EndTx`
6. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- Byte code lookup.
- Stack reads for `offset` and `length`. 
- Call context lookups for `is_success` and `rw_counter_end_of_reversion`.
- Restore context lookups for non-root call.

## Code
   Please refer to `src/zkevm_specs/evm/execution/error_code_store.py`.