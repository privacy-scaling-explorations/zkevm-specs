# BALANCE opcode

## Procedure

The `BALANCE` opcode gets balance of the given account.

## EVM behaviour

The `BALANCE` opcode pops `address` (20 bytes of data) off the stack and pushes
the balance of the corresponding account onto the stack. If the given account
doesn't exist, then it will push 0 onto the stack instead.

## Circuit behaviour

1. Construct call context table in rw table.
2. Do bus-mapping lookup for stack read, call context read and account read
   operations.
3. Do bus-mapping lookup for transaction access list write and stack write
   operations.

## Constraints

1. opId = 0x31
2. State transition:
   - gc + 7 (1 stack read, 1 stack write, 3 call context reads, 1 account reads,
     1 transaction access list write)
   - stack_pointer + 0 (one pop and one push)
   - pc + 1
   - gas:
     - the accessed `address` is warm: GAS_COST_WARM_ACCESS
     - the accessed `address` is cold: GAS_COST_ACCOUNT_COLD_ACCESS
3. Lookups: 7
   - `address` is popped from the stack.
   - 3 reads from call context for `tx_id`, `rw_counter_end_of_reversion`, and
     `is_persistent`.
   - `address` is added to the transaction access list if not already present.
   - `balance` is read from the given account. Set to 0 if it doesn't exist.
   - the `balance` result is pushed onto the stack.
4. Additional Constraints
   - value `is_warm` matches the gas cost for this opcode.

## Exceptions

1. stack underflow: if the stack starts empty
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/balance.py`.
