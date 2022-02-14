# CALLDATACOPY opcode

## Procedure

The `CALLDATACOPY` opcode pops `memory offset`, `data offset`, and `length` from the stack.
It then copies `length` bytes from call data buffer starting from `data offset` to memory at
address `memory offset`. EVM also left-pads 0 to the call data buffer in case the access to the
call data buffer is out of bound.

The gas cost of `CALLDATACOPY` opcode consists of two parts: constant cost 3 and dynamic cost.
The dynamic cost includes the memory expansion cost and copier cost in terms of the number of
words copied. Note that when `length = 0`, the memory expansion cost is 0 regardless of
`memory offset`.

## Circuit behaviour

Because the `length` is dynamic, it requires multiple step slots to fully verify the `CALLDATACOPY`.
In the `CALLDATACOPY` gadget, it constrains the stack pops, state transition, and lookups to
retrieve the additional information such as tx id, call data offset for internal calls, etc.
Then the gadget transits to an internal state called `CopyToMemory`, which can loop itself for
copying data to the memory if `length > 0`.

## Constraints

1. opId = 0x37
2. State transition:
   - rw_counter
        - +4 for root calls (3 stack read, 1 call context read)
        - +6 for internal calls (3 stack read, 3 call context read)
   - stack_pointer + 3
   - pc + 1
   - gas + 3 + dynamic cost (memory expansion and copier cost when `length > 0`)
   - memory_size
        - `max(prev_memory_size, (memory_offset + length + 31) / 32)` if `length > 0`
        - `prev_memory_size` if `length = 0`.
3. Lookups: 5 (root calls) or 6 (internal calls)
   - `memory_offset` is at the top of the stack
   - `data_offset` is at the second position of the stack
   - `length` is at the third position of the stack
   - `tx_id` is in the rw table (call context)
   - for root calls (`is_root = 1`):
        - `call_data_length` is in the tx table
   - for internal calls (`is_root = 0`):
        - `call_data_length` is in the rw table (call context)
        - `call_data_offset` is in the rw table (call context)

## Exceptions

1. stack underflow: `1021 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/calldatacopy.py`.
