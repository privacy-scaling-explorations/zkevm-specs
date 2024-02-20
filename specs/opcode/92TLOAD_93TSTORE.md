# TLOAD & TSTORE opcodes

## Constraints

1. opcodeId checks
   1. opId === OpcodeId(0x5c) for `TLOAD`
   2. opId === OpcodeId(0x5d) for `TSTORE`
2. state transition:
   - gc
     - `TLOAD`: +7
       - 4 call_context read
       - 2 stack operations
       - 1 transient storage reads
     - `TSTORE`: +8
       - 5 call_context read
       - 2 stack operations
       - 1 transient storage reads/writes
   - stack_pointer
     - `TLOAD`: remains the same
     - `TSTORE`: -2
   - pc + 1
   - reversible_write_counter
     - `TLOAD`: +0
     - `TSTORE`: +1 (for transient storage)
   - gas:
     - `TLOAD`:
       - gas + 100
     - `SSTORE`:
       - gas + 100
3. lookups:
   - `TLOAD`: 8 busmapping lookups
     - call_context:
       - `tx_id`: Read the `tx_id` for this tx.
       - `rw_counter_end_of_reversion`: Read the `rw_counter_end` if this tx get reverted.
       - `is_persistent`: Read if this tx will be reverted.
       - `callee_address`: Read the `callee_address` of this call.
     - stack:
       - `key` is popped off the top of the stack
       - `value` is pushed on top of the stack
     - transient storage: The 32 bytes of `value` are read from storage at `key`
   - `TSTORE`: 10 busmapping lookups
     - call_context:
       - `tx_id`: Read the `tx_id` for this tx.
       - `is_static`: Read the call's property `is_static`
       - `rw_counter_end_of_reversion`: Read the `rw_counter_end` if this tx get reverted.
       - `is_persistent`: Read if this tx will be reverted.
       - `callee_address`: Read the `callee_address` of this call.
     - stack:
       - `key` is popped off the top of the stack
       - `value` is popped off the top of the stack
     - transient storage:
       - The 32 bytes of new `value` are written to transient storage at `key`, with the previous `value` and `committed_value`

## Exceptions

1. gas out: remaining gas is not enough
2. stack underflow:
   - the stack is empty: `1024 == stack_pointer`
   - only for `TSTORE`: contains a single value: `1023 == stack_pointer`
3. context error
   - only for `TSTORE`: the current execution context is from a `STATICCALL` (since Cancun fork).
