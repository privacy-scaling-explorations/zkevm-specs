# SLOAD & SSTORE op code

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x54) for `SLOAD`
   2. opId === OpcodeId(0x55) for `SSTORE`
2. state transition:
   - gc
     - `SLOAD`/`SSTORE`:  +3 (2 stack operations + 1 storage reads/writes)
   - stack_pointer
     - `SLOAD`: remains the same
     - `SSTORE`: -2
   - pc + 1
   - gas:
     - `SLOAD`:
       + the accessed address is warm: gas + 100
       + the accessed address is cold: gas + 2100
     - `SSTORE`:
       + the accessed address is warm:
         * `new_value == current_value`: gas + 100 + 100
         * `new_value != current_value`:
           - `current_value == last_tx_value`:
             - `last_tx_value == 0`: gas + 20000 + 100
             - `last_tx_value != 0`: gas + 2900 + 100
           - `current_value != last_tx_value`: gas + 100 + 100
       + the accessed address is cold:
         * `new_value == current_value`: gas + 100 + 2900
         * `new_value != current_value`:
           - `current_value == last_tx_value`:
             - `last_tx_value == 0`: gas + 20000 + 2900
             - `last_tx_value != 0`: gas + 2900 + 2900
           - `current_value != last_tx_value`: gas + 100 + 2900
3. lookups:
   - `SLOAD`/`SSTORE`: 3 busmapping lookups
     - stack:
       - `address` is popped off the top of the stack
       - `value`
         - is pushed on top of the stack for `SLOAD`
         - is popped off the top of the stack for `SSTORE`
     - storage:
       - `SLOAD`: The 32 bytes of `value` are read from storage at `address`.
       - `SSTORE`: The 32 bytes of `value` are written to storage at `address`. Revert if gas out.

## Exceptions

1. gas out: remaining gas is not enough
2. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `SSTORE`: contains a single value: `1023 == stack_pointer`
3. context error
   - only for `SSTORE`: the current execution context is from a `STATICCALL` (since Byzantium fork).
