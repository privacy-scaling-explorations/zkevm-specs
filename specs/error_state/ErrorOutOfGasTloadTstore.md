# ErrorOutOfGasTloadTstore state for both TLOAD and TSTORE OOG errors

## Procedure

Handle the corresponding out of gas errors for both `TLOAD` and `TSTORE` opcodes.

### EVM behavior

The out of gas error may occur for `constant gas`.

#### TLOAD gas cost

For this gadget, TLOAD gas cost in EIP-1153 is specified as the cost of hot SLOAD, currently `100`.

#### TSTORE gas cost

For this gadget, TSTORE gas cost in EIP-1153 is specified as the cost of SSTORE on an already SSTOREd slot, currently `100`.

### Constraints

1. For TLOAD, constrain `gas_left < gas_cost`.
2. For TSTORE, constrain `gas_left < gas_cost`.
3. Only for TSTORE, constrain `is_static == false`.
4. Current call must fail.
5. If it's a root call, it transits to `EndTx`.
6. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
7. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

### Lookups

7 bus-mapping lookups for TLOAD and 8 for TSTORE:

1. 5 call context lookups for `tx_id`, `is_static`, `callee_address`, `is_success` and `rw_counter_end_of_reversion`.
2. 1 stack read for `transient_storage_key`.
3. Only for TSTORE, 1 stack read for `value_to_store`.
4. Only for TSTORE, 1 account transient storage read.

## Code

> TODO