# BEGIN_TX 

## Procedure

The `begin_tx` gadget performs preliminary checks on a transaction and its caller's account as well as further checks depending on the transaction type. 

More particularly, for all transactions, we make sure that the account nonce is incremented by 1 if the tx is valid, and that the caller address is not null. We also verify that a transaction is set as invalid if and only if there is either not enough gas, the tx's nonce is not the same as caller's account previous nonce or the balance is insufficient.

Depending whether the transaction is a Create, calls a precompile or calls an account with or without code, the checks as well as the number of lookups vary.

## Constraints

1. If this is the first transaction, check the transaction id is set to 1
-> `tx_id = 1`
2. Check the transaction's caller's address is not null
-> `tx_caller_address != 0`
3. If the transaction is valid, check the account nonce has been incremented correctly otherwise is the same
-> `account_nonce - account_nonce_prev - 1 + is_tx_invalid = 0`
4. Initilialise transactions's access list with caller's, callee's and coinbase's address
5. Verify transfer with `tx_value` and `gas_fee` or 0s if tx is invalid
6. Assert is_tx_invalid is correct
-> `is_tx_invalid  - 1 - (1 - balance_not_enough) * (1 - gas_not_enough) * (is_nonce_valid) = 0`
7. if tx is a create `Condition(tx_is_create - 1 = 0)`
    1. if tx is invalid or call data is 0 `Condition(is_tx_invalid - 1 = 0 ||  tx_call_data_length = 0)`
        1. Ensure is_persistent is set to 1
        -> `reversion_info.is_persistent - 1 = 0`
        2. Ensure next instruction is endTx
        3. Constrain state transition with current rw counter
    2. Otherwise
        1. Setup next call's context
        2. Constrain state transition to new context 
7. elif we call a precompile raise error NotImplementedError
7. else
    1. if tx is invalid or code hash is empty `Condition(is_tx_invalid - 1 = 0 ||  is_empty_code_hash = 1)`
        1. Assert tx is persistant `reversion_info.is_persistent - 1 = 0`
        2. Ensure next instruction is endTx
        3. Constrain state transition with current rw counter
    1. Otherwise
        1. Setup next call's context 
        2. Constrain state transition to new context 

Consummed gas: tx_calldata_gas_cost + tx_accesslist_gas + !is_create * GAS_COST_TX  + is_create * (GAS_COST_CREATION_TX + len_words * GAS_COST_INITCODE_WORD)

### Lookups

/!\ Precompiles are not handled yet

#### RW accesses
In common, for all cases: 
- CallContext TxId
- CallContext RwCounterEndOfReversion (done through instruction.reversion_info)
- CallContext IsPersistent (done through instruction.reversion_info)
- CallContext IsSuccess
- StateWrite adding caller's address to Tx access list
- StateWrite adding callee's address to Tx access list
- StateWrite adding coinbase address to Tx access list
- AccountWrite caller's Nonce
- AccountWrite caller's Balance (done through instruction.transfer_with_gas_fee) 
- AccountWrite callee's Balance (done through instruction.transfer_with_gas_fee)

If tx is not a Create, we do an additional
- AccountRead AccountFieldTag.CodeHash

Finally, if the tx is valid and either is a create with call data or the callee is a contract (that is callee.code_hash is not null), we do these extra checks:
- CallContext Depth
- CallContext CallerAddress
- CallContext CalleeAddress
- CallContext CallDataOffset
- CallContext CallDataLength
- CallContext Value
- CallContext IsStatic
- CallContext LastCalleeId
- CallContext LastCalleeReturnDataOffset
- CallContext LastCalleeReturnDataLength
- CallContext IsRoot
- CallContext IsCreate
- CallContext CodeHash

Hence, the rw_counter is
- isCreate = 1
    - invalid or tx_call_data_length = 0: 10
    - otherwise: 23
- isCreate = 0:
    - invalid: 11
    - otherwise: 24
    
#### Other Lookups
- BlockContext Coinbase
- TxContext Caller Address
- TxContext Callee Address
- TxContext IsCreate
- TxContext Value
- TxContext CallDataLength
- TxContext TxInvalid
- TxContext Nonce
- TxContext Gas
- TxContext CallDataGasCost
- TxContext AccessListGasCost
- CopyLookup TxCalldata - RlcAcc (if is not create)
- CopyLookup TxCalldata - Bytecode (if is not create)

## Exceptions

## Code

Please refer to [codesize.py](src/zkevm_specs/evm_circuit/execution/begin_tx.py).
