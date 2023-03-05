# ErrorOutOfGasMemoryCopy state

## Procedure

Handle the corresponding out of gas errors for `CALLDATACOPY`, `CODECOPY`, `EXTCODECOPY` and `RETURNDATACOPY` opcodes.

### EVM behavior

For the current `go-ethereum` code, the out of gas error may occur for `constant gas` or `dynamic gas`. The gas cost is calculated as:

```
gas_cost = constant_gas + dynamic_gas
```

The constant gas is same for `CALLDATACOPY`, `CODECOPY` and `RETURNDATACOPY`.

```
constant_gas = 3
```

According to EIP-2929, the constant gas of `EXTCODECOPY` is different for cold and warm accounts.

```
if is_warm:
    constant_gas = 100
else:
    constant_gas = 2600
```

They are also same for dynamic gas calculation. As each of `CALLDATACOPY`, `CODECOPY` and `RETURNDATACOPY` has `3` stack read values as `destination_offset`, `source_offset` and `copy_byte_size`. `EXTCODECOPY` also has these `3` stack read values (and `1` extra `external_address`). The dynamic gas is calculated as:

```
copy_word_size = (copy_byte_size + 31) // 32

dynamic_gas = copy_word_size * 3

# Note that opcodes with a byte size parameter of 0 will not trigger memory expansion,
# regardless of their offset parameters.
if copy_word_size > 0:
    dynamic_gas = dynamic_gas + memory_expansion_gas_cost
```

The memory expansion gas cost is calculated as:

```
next_memory_word_size = (destination_offset + copy_byte_size + 31) // 32

# `current_memory_word_size` is fetched from the execution step.
if next_memory_word_size <= current_memory_word_size:
    memory_expansion_gas_cost = 0
else:
    memory_expansion_gas_cost = (
        3 * (next_memory_word_size - current_memory_word_size)
        + next_memory_word_size * next_memory_word_size // 512
        - current_memory_word_size * current_memory_word_size // 512
    )
```

### Constraints

1. Constrain `gas_left < gas_cost`.
2. Current call must fail.
3. If it's a root call, it transits to `EndTx`.
4. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
5. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

### Lookups

`5` basic bus-mapping lookups:

. `3` stack pop `destination_offset`, `source_offset` and `copy_byte_size`.
. `2` call context lookups for `is_success` and `rw_counter_end_of_reversion`.

`EXTCODECOPY` has extra `3` bus-mapping lookups:

. `1` stack pop for `external_address`.
. `1` call context lookup for `tx_id`.
. `1` account access list read for `is_warm`.

And restore context lookups for non-root call.
