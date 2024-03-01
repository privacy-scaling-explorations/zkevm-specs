# END_TX 

## Procedure

The `end_tx` gadget handles refund and coinbase tip as well as cumulative gas within a block. 


## Constraints

1. Calculate effective refund (c.f. below list)
2. Add [(effective_refund + gas_left) * gas_price] back to caller's balance
3. Check effective tip = tx gas price - base fee
4. Add gas_used * effective_tip to coinbase's balance (and create coinbase account if needs be)
5. End transaction
    1. Check that the current cumulative gas used is null if this is the 1st transaction else corresponds to previous transaction's
    2. Increase cumulative gas used by the gas used
    3. If the next execution state is BeginTx
        1. The next transaction's id is correctly incremented
        2. Transition to new context (rw_counter =  9 + transfer.rw - is_first_tx)
    4. Elif the next execution step is EndBlock
        1. Transition to new context (rw_counter =  9 + transfer.rw - is_first_tx, and same call id)

Gas refund: it is capped to  gas_used // MAX_REFUND_QUOTIENT_OF_GAS_USED (c.f. EIP 3529)

### Lookups

#### RW accesses
In all cases, we bump read-write-counter by 9 + transfer.rw - is_first_tx:
- CallContext TxId
- CallContext IsPersistent
- RWLookup Read TxRefund
- AccountRead coinbase's codehash
- UpdateBalance
    - AccountWrite caller's balance
- TransferTo
    - AccountWrite coinbase's balance
- EndTx
    - RWLookup Write TxReceipt.PostStateOrStatus
    - RWLookup Write TxReceipt.LogLength
    - RWLookup Write current transaction's TxReceipt.CumulativeGasUsed
    - If not first tx, RWLookup Read previous transaction's TxReceipt.CumulativeGasUsed
    - If next execution state is BeginTx, CallContext TxId (does not increase rw counter)


#### Other Lookups
- TxContext Gas
- TxContext GasPrice
- TxContext CallerAddress
- BlockContext BaseFee
- BlockContext Coinbase

## Exceptions