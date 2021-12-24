# SLOAD & SSTORE op code

## Cross-tx

TODO:

## Inner-tx

### Constraints

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
     - `SLOAD`: gas + 200
     - `SSTORE`:
       + (value != 0) && (storage_location == 0): gas + 20000
       + (value == 0) || (storage_location != 0): gas + 5000
3. lookups:
   - `SLOAD`/`SSTORE`: 3 busmapping lookups
     - stack:
       - `address` is popped off the top of the stack
       - `value`
         - is pushed on top of the stack for `SLOAD`
         - is popped off the top of the stack for `SSTORE`
     - storage:
       - `SLOAD`/`SSTORE`: The 32 bytes of `value` are read/written from/to storage at `address`.

### Exceptions

1. gas out: remaining gas is not enough
2. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `SSTORE`: contains a single value: `1023 == stack_pointer`
