# BEGIN_TX 

## Procedure

The `begin_tx` gadget performs preliminary checks on a transaction and its caller's account as well as further checks depending on the transaction type. 

More particularly, for all transactions, we make sure that the account nonce is incremented by 1 if the tx is valid, and that the caller address is not null. We also verify that a transaction is set as invalid if and only if there is either not enough gas, the tx's nonce is not the same as caller's account previous nonce or the balance is insufficient.

Depending whether the transaction is a CREATE, calls a precompile or calls an account with or without code, the checks as well as the number of lookups vary.

## Constraints
/!\ Call to precompiles are not handled yet

1. The transaction id is set to 1 if this is the first step.
2. Calculate the transaction gas fee (gas price * gas + tx value = cost sum )
3. The transaction is successful (lookup to CallContextFieldTag::IsSuccess with reversion_info.is_persistent)
4. The transaction is valid
    1. The gas is sufficient (tx.gas > tx.intrinsic_gas)
    2. The balance is sufficient (gas limit > gas used, handled when transferring gas)
    3. The nonce is valid (caller's previous nonce = tx.nonce)
5. The access list of the transaction is initialised with the addresses of the caller, callee, coinbase and precompiles
6. The caller's address is not null
7. The caller's nonce is incremented (caller.nonce = tx.nonce + 1)
8. The callee's codehash is correct
9. Transfer the gas (reversible)
10. If the transaction is a CREATE
    1. Create the contract
    2. The callee's address is correctly initialised from the caller's nonce
    3. The callee's nonce is correctly initialised (reversible)
    4. The contract's caller address is correctly initialised
    5. The contract's caller nonce is correctly initialised
    6. Transition to new context (reversible_write_counter = transfer.reversible + 1, rw_counter = 23 + transfer.rw + #precompiles)
11. Else (call to account)
    1. The callee's address is not null
    2. If the account called has no code (empty code hash or account does not exist (i.e. code_hash = 0))
        1. The transaction is persistant
        2. The next execution state is endTx
        3. Transition to new context (rw_counter = 9 + transfer.rw + #precompiles)
    3. Else (call to account with code)
        1. Transition to new context (reversible_write_counter = transfer.reversible, rw_counter = 22 + transfer.rw + #precompiles)
12. (TODO. Call to precompile)

Consummed gas: tx_calldata_gas_cost + tx_accesslist_gas + !is_create * GAS_COST_TX  + is_create * (GAS_COST_CREATION_TX + len_words * GAS_COST_INITCODE_WORD)

### Lookups

#### RW accesses
In all cases, we bump read-write-counter by 9 + #transfer:
- BeginTxHelper
    - CallContext TxId
- CallContext RwCounterEndOfReversion (done through reversion_info)
- CallContext IsPersistent (done through reversion_info)
- CallContext IsSuccess
- StateWrite adding caller's address to Tx access list
- StateWrite adding callee's address to Tx access list
- StateWrite adding coinbase address to Tx access list
- StateWrite adding precompile addresses to Tx access list    #precompile
- AccountWrite caller's Nonce
- AccountRead calee's CodeHash
- TransferWithGasFee (reversible)
    - AccountWrite caller's Balance 
    - AccountWrite callee's Balance

If tx is CREATE, we also bump read-write-counter by 1:
- AccountWrite callee's Nonce (reversible)

If tx is not a contract call with no code, we also bump read-write-counter by 13:
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
    
#### Other Lookups
- TxData
    - TxContext Nonce
    - TxContext Gas
    - TxContext IsCreate
    - TxContext CallDataLength
    - TxContext CallDataGasCost
    - TxContext GasPrice
    - TxContext Value
    - TxContext Caller Address
    - TxContext Callee Address
- BlockContext Coinbase
- KeccakTable create.input_rlc

## Exceptions