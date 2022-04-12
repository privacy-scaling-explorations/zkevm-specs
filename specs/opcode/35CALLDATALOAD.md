# CALLDATALOAD opcode

## Procedure

The `CALLDATALOAD` opcode gets input data of current environment.

## EVM Behaviour

Stack input is the byte offset to read call data from. Stack output is a 32-byte value starting from the given offset of the call data. All bytes after the end of the call data are set to `0`.

## Constraints

1. opId == 0x35
2. State Transition:
   - if is_root_call:
     - rw_counter += 4 (1 stack read, 2 call context read, 1 stack write)
   - if is_internal_call:
     - rw_counter += rw_counter_offset ∈ {5, 6, ..., 36, 37} (1 stack read, 3 call context reads, i ∈ {0, 1, ..., 31, 32} memory reads, 1 stack write)
   - stack_pointer unchanged
   - pc + 1
   - gas - 3
3. Lookups:
   - `offset` is at the top of the stack
   - if is_root_call (where `src_addr = offset`):
     - `tx_id` is in the RW table (call context)
     - `calldata_length` is in the RW table (call context)
     - i ∈ {0, 1, ..., 31, 32} lookups for `i in range(32)`: if `buffer.read_flag(i)` then the i'th byte of the element on top of the stack `calldata_word[i]` is in the TX table {tx id, call data, src_addr + i}
   - if is_internal_call (where `src_addr = offset + calldata_offset`):
     - `calldata_length` is in the RW table (call context)
     - `calldata_offset` is in the RW table (call context)
     - `caller_id` is in the RW table (call context)
     - i ∈ {0, 1, ..., 31, 32} lookups for `i in range(32)`: if `buffer.read_flag(i)` then the i'th byte of the element on top of the stack `calldata_word[i]` is in the RW table {memory, src_addr + i, caller_id}

## Exceptions

1. Stack underflow: stack is empty, stack pointer = 1024
2. Out of gas: remaining gas is not enough for this opcode

## Code

Please refer to `src/zkevm_specs/evm/execution/calldataload.py`.
