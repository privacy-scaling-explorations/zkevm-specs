# END_TX 

## Procedure

The `end_tx` gadget performs preliminary checks on a transaction and its caller's account as well as further checks depending on the transaction type. 

More particularly, for all transactions, we make sure that the account nonce is incremented by 1 if the tx is valid, and that the caller address is not null. We also verify that a transaction is set as invalid if and only if there is either not enough gas, the tx's nonce is not the same as caller's account previous nonce or the balance is insufficient.

Depending whether the transaction is a Create, calls a precompile or calls an account with or without code, we do the following,
- isCreate = 1
- calling Precompile
- Call to account with empty code
- Call to account with code

## Constraints

1. If the transaction is invalid, check the refund is null
-> `(1 - is_tx_invalid) * effective_refund = 0`
2. Add effective_refund * gas_price back to caller's balance
3. Add gas_used * effective_tip to coinbase's balance
4. Constrain tx status matches with `PostStateOrStatus`
5. Constrain log id matches with `LogLength` of TxReceipt tag in RW
6. If tx is invalid, assert log_id is 0
7. Constrain `CumulativeGasUsed` of TxReceipt tag in RW to 0 if is first tx otherwise previous `CumulativeGasUsed + gas_used`
8. if next execution state is begin_tx
    1. Assert tx_id is incremented by 1
    2. Constrain state transition with rw_counter =  10 - is_first_tx
9. if next execution step is EndBlock
    1. Constrain state transition with rw_counter =  9 - is_first_tx and same call_id

### Lookups

/!\ Precompiles are not handled yet

#### RW accesses
In common, for all cases: 
- CallContext TxId
- CallContext IsPersistent
- RWLookup Read TxRefund
- AccountWrite caller's balance
- AccountWrite coinbase's balance
- RWLookup Write TxReceipt.PostStateOrStatus
- RWLookup Write TxReceipt.LogLength
- RWLookup Write TxReceipt.CumulativeGasUsed

If not first tx,
- RWLookup Read TxReceipt.CumulativeGasUsed

If next execution state is begin_tx,
- CallContext TxId

Hence, the rw_counter is: 8 + 1 * !is_first_tx + 1 * (next execution state = begin_tx)

#### Other Lookups
- TxContext TxInvalid
- TxContext Gas    
- TxContext CallerAddress
- BlockContext BlockContext.BaseFee
- BlockContext BlockContext.Coinbase

## Exceptions


## Code

Please refer to [codesize.py](src/zkevm_specs/evm_circuit/execution/end_tx.py).
