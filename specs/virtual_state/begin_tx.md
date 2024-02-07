# BEGIN_TX 

## Procedure

The `begin_tx` gadget performs preliminary checks on a transaction and its caller's account as well as further checks depending on the transaction type. 

More particularly, for all transactions, we make sure that the account nonce is incremented by 1 if the tx is valid, and that the caller address is not null. We also verify that a transaction is set as invalid if and only if there is either not enough gas, the tx's nonce is not the same as caller's account previous nonce or the balance is insufficient.

Depending whether the transaction is a Create, calls a precompile or calls an account with or without code, we do the following,
- isCreate = 1
- calling Precompile
- Call to account with empty code
- Call to account with code

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


### Lookups accesses
In common, for all cases: 
- CallContext TxId
- CallContext IsSuccess
- BlockContext Coinbase
- TxContext CallerAddress
- TxContext CalleeAddress
- TxContext IsCreate
- TxContext Value
- TxContext CallDataLength
- TxContext TxInvalid
- TxContext Nonce
- AccountWrite Nonce 
- TxContext Gas
- TxContext CallDataGasCost
- TxContext AccessListGasCost

if is Create, valid and data length != 0
- copyLookup CopyDataTypeTag.RlcAcc
- copyLookup CopyDataTypeTag.ByteCode
- keccak_lookup CopyDataTypeTag.RlcAcc
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

If not create nor precompile
- Account read   AccountFieldTag.CodeHash
if code hash not empty and tx valid 
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


## Exceptions

1. `NotImplementedError` when calling a precompile

## Code

Please refer to [codesize.py](src/zkevm_specs/evm_circuit/execution/begin_tx.py).
