# EXTCODECOPY opcode

## Procedure

The `EXTCODECOPY` opcode pops `address`, `memory_offset`, `code_offset` and `size` from the stack. It then copies `size` bytes of code of `address` from an offset `code_offset` to the memory at the address `memory_offset`. For out-of-bound scenarios where `size > len(code) - code_offset`, EVM pads 0 to the end of the copied bytes.

The gas cost of `EXTCODECOPY` opcode is dynamic and is based on the cost of memory expansion and copying (variable depending on the `size` copied to memory) and accessing the address (variable depending on whether the `address` is warm or not)

## Circuit Behaviour

The `EXTCODECOPY` circuit constrains the values popped from stack, call context/address read lookups and CopyTable lookups to verify the copy of bytes. The copy of a dynamic number of bytes is verified by the CopyCircuit outside the `EXTCODECOPY` gadget.

## Constraints

1. opId = 0x3c
2. State transition:
   - stack pointer + 4
   - pc + 1
   - gas -> dynamic gas cost
   - memory_size
      - `prev_memory_size` if `size = 0`
      - `max(prev_memory_size, (memory_offset + size + 31) / 32)` if `size > 0`
3. Lookups: 10
   - `address` is at the top of the stack
   - `memory_offset` is at the second position of the stack
   - `code_offset` is at the third position of the stack
   - `size` is at the fourth position of the stack
   - `code_hash` from the address (will be 0 when the account doesn't exist).
   - `code_size` from the bytecode table if account exists (`code_hash != 0`)
   - `tx_id`, `rw_counter_end_of_reversion`, `is_persistent` from call context
   - `address` is added to the transaction access list if not already present

## Exceptions

1. Stack Underflow: `1020 <= stack pointer <= 1024`
2. Out-of-Gas: remaining gas is not enough

## Code

Please refer to [extcodecopy](src/zkevm_specs/evm/execution/extcodecopy.py).
