# SLOAD & SSTORE op code

## Variables definition

| Name | Value |
| - | - |
| COLD_SLOAD_COST | 2100 |
| WARM_STORAGE_READ_COST | 100 |
| SLOAD_GAS | 100 |
| SSTORE_SET_GAS | 20000 |
| SSTORE_RESET_GAS | 2900 |
| SSTORE_CLEARS_SCHEDULE | 15000 |

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x54) for `SLOAD`
   2. opId === OpcodeId(0x55) for `SSTORE`
2. state transition:
   - gc
     - `SLOAD`: +5 (2 stack operations + 1 storage reads + 2 access_list reads/writes)
     - `SSTORE`: +9
       + 2 stack operations
       + 1 original value read
       + 2 storage reads/writes
       + 2 access_list reads/writes
       + 2 gas_refund reads/writes
   - stack_pointer
     - `SLOAD`: remains the same
     - `SSTORE`: -2
   - pc + 1
   - state_write_counter
       - `SLOAD`: +1
       - `SSTORE`: +2
   - gas:
     - `SLOAD`:
       + the accessed address is warm: gas + WARM_STORAGE_READ_COST
       + the accessed address is cold: gas + COLD_SLOAD_COST
     - `SSTORE`:
       + the accessed address is warm:
         * `current_value == new_value`: gas + SLOAD_GAS
         * `current_value != new_value`:
           - `original_value == current_value`:
             - `original_value == 0`: gas + SSTORE_SET_GAS
             - `original_value != 0`: gas + SSTORE_RESET_GAS
           - `original_value != current_value`: gas + SLOAD_GAS
       + the accessed address is cold:
         * `current_value == new_value`: gas + SLOAD_GAS + COLD_SLOAD_COST
         * `current_value != new_value`:
           - `original_value == current_value`:
             - `original_value == 0`: gas + SSTORE_SET_GAS + COLD_SLOAD_COST
             - `original_value != 0`: gas + SSTORE_RESET_GAS + COLD_SLOAD_COST
           - `original_value != current_value`: gas + SLOAD_GAS + COLD_SLOAD_COST
   * gas_refund:
     - `SSTORE`:
       + `current_value != new_value`:
         * `original_value == current_value`:
           * `original_value != 0` && `new_value == 0`: gas_refund + SSTORE_CLEARS_SCHEDULE
         * `original_value != current_value`:
           * `original_value != 0`:
             - `current_value == 0`: gas_refund - SSTORE_CLEARS_SCHEDULE
             - `new_value == 0`: gas_refund + SSTORE_CLEARS_SCHEDULE
           * `original_value == new_value`:
             - `original_value == 0`: gas_refund + SSTORE_SET_GAS - SLOAD_GAS
             - `original_value != 0`: gas_refund + SSTORE_RESET_GAS - SLOAD_GAS
3. lookups:
   - `SLOAD`/`SSTORE`: 5 busmapping lookups
     - stack:
       - `address` is popped off the top of the stack
       - `value`
         - is pushed on top of the stack for `SLOAD`
         - is popped off the top of the stack for `SSTORE`
     - storage:
       - `SLOAD`: The 32 bytes of `value` are read from storage at `address`.
       - `SSTORE`: The 32 bytes of `value` are written to storage at `address`.
     - access_list:
       - `SLOAD`: Whether the address is warm (accessed before), mark as warm afterward.
       - `SSTORE`: Whether the address is warm (accessed before), mark as warm afterward.

## Exceptions

1. gas out: remaining gas is not enough
2. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `SSTORE`: contains a single value: `1023 == stack_pointer`
3. context error
   - only for `SSTORE`: the current execution context is from a `STATICCALL` (since Byzantium fork).
