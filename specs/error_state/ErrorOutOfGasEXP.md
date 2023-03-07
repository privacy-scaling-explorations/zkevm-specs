# ErrorOutOfGasEXP state for EXP OOG error

## Procedure

Handle the corresponding out of gas error for `EXP`.

### EVM behavior

The EXP gas cost is calculated as:

```
# `exponent.bits()` returns the least number of bits needed to represent exponent.
exponent_byte_size = (exponent.bits() + 7) // 8

gas_cost = exponent_byte_size * 50 + 10
```

### Constraints

1. Constrain `gas_left < gas_cost`.
2. Current call must fail.
3. If it's a root call, it transits to `EndTx`.
4. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
5. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

### Lookups

4 basic bus-mapping lookups + restore context lookups (for non-root call):

1. 2 stack read for `base` and `exponent`.
2. 2 call context lookups for `is_success` and `rw_counter_end_of_reversion`.
3. Restore context lookups for non-root call.
