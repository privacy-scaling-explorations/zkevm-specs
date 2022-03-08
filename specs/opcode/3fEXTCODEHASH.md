# EXTCODEHASH opcode

## Procedure

The `EXTCODEHASH` opcode pops `address` off the stack and pushes the code hash
of the corresponding account onto the stack. If the corresponding account is
empty (i.e. has nonce = 0, balance = 0 and no code), then it will push 0 onto
the stack instead.

## Constraints

1. opId = 0x3f
2. State transition:
   - gc + 7 (1 stack read, 1 stack write, 1 call context read, 3 account reads,
     1 transaction access list write)
   - stack_pointer + 0 (one pop and one push)
   - pc + 1
   - gas:
     - the accessed `address` is warm: WARM_STORAGE_READ_COST
     - the accessed `address` is cold: COLD_ACCOUNT_ACCESS_COST
3. Lookups: 7
   - `address` is popped from the stack
   - tx id of call context is `tx_id`
   - `address` is added to the transaction access list if not already present
   - nonce of account is `nonce`
   - balance of account is `balance`
   - code hash of account is `code_hash`
   - if the account is (non)empty, (`code_hash`) 0 is pushed onto the stack
4. Additional Constraints
   - value `is_warm` matches the gas cost for this opcode
   - `is_empty` is boolean and 1 iff the account is empty

## Exceptions

1. stack underflow: if the stack starts empty
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/extcodehash.py`.
