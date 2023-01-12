# EXTCODEHASH opcode

## Procedure

The `EXTCODEHASH` opcode pops `address` off the stack and pushes the code hash
of the corresponding account onto the stack. If the corresponding account
doesn't exist then it will push 0 onto the stack instead.  Since we use
`code_hash = 0` to encode non-existing accounts, we can use the lookup result
directly.

## Constraints

1. opId = 0x3f
2. State transition:
   - gc + 7 (1 stack read, 1 stack write, 3 call context reads, 1 account read,
     1 transaction access list write)
   - stack_pointer + 0 (one pop and one push)
   - pc + 1
   - gas:
     - the accessed `address` is warm: WARM_STORAGE_READ_COST
     - the accessed `address` is cold: COLD_ACCOUNT_ACCESS_COST
3. Lookups: 7 busmapping lookups
   - `address` is popped from the stack
   - 3 from call context for `tx_id`, `rw_counter_end_of_reversion`, and
     `is_persistent`.
   - `address` is added to the transaction access list if not already present.
   - lookup account `code_hash`.
   - The EXTCODEHASH result is at the new top of the stack.
4. Additional Constraints
   - value `is_warm` matches the gas cost for this opcode.

## Exceptions

1. stack underflow: if the stack starts empty
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/extcodehash.py`.
