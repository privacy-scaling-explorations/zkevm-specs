# ErrorOutOfGasSHA3 state

## Procedure

Handle the corresponding out of gas errors for `SHA3`.

### EVM behavior

The `SHA3` gas cost is calculated as:

```
minimum_word_size = (size + 31) // 32

static_gas = 30
dynamic_gas = 6 * minimum_word_size + memory_expansion_cost
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

1. Stack reads `offset` and `size` for gas calculation
2. Constrain `gas_left < gas_cost`.
3. Current call must fail.
4. If it's a root call, it transits to `EndTx`.
5. If it isn't a root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.
6. Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_oog_sha3.py`.
