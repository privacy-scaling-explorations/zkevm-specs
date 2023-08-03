# ErrorOutOfGasCreate state

## Procedure

Handle the corresponding out of gas errors for `CREATE` and `CREATE2` opcodes.

### EVM behavior

The gas cost of `CREATE`/`CREATE2` is:
```
GAS_COST_CREATE := 32000
KECCAK_WORD_GAS_COST := 6
GAS_COST_INITCODE_WORD := 2

keccak_gas_cost = KECCAK_WORD_GAS_COST * size if op_id == CREATE2 else 0
initcode_gas_cost = GAS_COST_INITCODE_WORD * size
gas_cost = (
    GAS_COST_CREATE
    + memory_expansion_gas_cost
    + keccak_gas_cost
    + initcode_gas_cost
)

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

1. Current opcode is `CREATE` or `CREATE2`.
2. `gas_left < gas_cost`.
3. Current call fails.
4. Common error constraints: 
  - Current call fails. 
  - Constrain `rw_counter_end_of_reversion = rw_counter_end_of_step + reversible_counter`.
  - If it's a root call, it transits to `EndTx`.
  - If it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_oog_create.py`.
