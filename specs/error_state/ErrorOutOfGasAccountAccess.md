# ErrorOutOfGasAccountAccess state.

## Procedure

Handle the corresponding out of gas error for `BALANCE`  | `EXTCODESIZE` | `EXTCODEHASH`.

### EVM behavior

The three opcodes ( `BALANCE`  | `EXTCODESIZE` | `EXTCODEHASH`) share the same gas cost model:

```
let gas_cost = if is_warm {
            GasCost::WARM_ACCESS
        } else {
            GasCost::COLD_ACCOUNT_ACCESS
        };

```
`is_warm` indicates target tx account is in account access list or not. 

### Constraints

1. opcode must be one of  `BALANCE`  | `EXTCODESIZE` | `EXTCODEHASH`
2. Constrain `gas_left < gas_cost`.
3. Current call must fail.
4. If it's a root call, it transits to `EndTx`.
5. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
6. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

### Lookups

5 basic bus-mapping lookups + restore context lookups (for non-root call):

1. 1 stack read for `address` + 1 tx id lookup + 1 account access list read.
2. 2 call context lookups for `is_success` and `rw_counter_end_of_reversion`.
3. Restore context lookups for non-root call.
