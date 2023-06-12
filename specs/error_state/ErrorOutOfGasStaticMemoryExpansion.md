# ErrorOOGStaticMemoryExpansion state

## Procedure

Handle the corresponding out of gas errors for `MLOAD`, `MSTORE` and `MSTORE8` opcodes.

### EVM behavior

For the current `go-ethereum` code, the out of gas error may occur for `constant gas` or `dynamic gas`. The gas cost is calculated as:

```
gas_cost = constant_gas + dynamic_gas
```

The constant gas is same for `MLOAD`, `MSTORE` and `MSTORE8`.

```
constant_gas = 3
```

They are also same for dynamic gas calculation. The dynamic gas is calculated as:

```
dynamic_gas = memory_expansion_cost
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

1. Current opcode is one of `MLOAD`, `MSTORE` and `MSTORE8`.
2. Constrain `gas_left < gas_cost`.
3. Current call must fail.
4. If it's a root call, it transits to `EndTx`.
5. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
6. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

### Lookups

1. `1` stack pop.
2. `2` call context lookups for `is_success` and `rw_counter_end_of_reversion`.

And restore context lookups for non-root call.