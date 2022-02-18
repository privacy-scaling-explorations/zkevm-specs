# CALLDATALOAD opcode

## Procedure

The `CALLDATALOAD` opcode pops `offset` from the stack.
It then copies 32 bytes from call data buffer starting at the position `offset` to the Stack. 
EVM also pads 0's to the end of call data buffer in the case of out-of-bound access to the call data buffer.

## Circuit behaviour

In the `CALLDATALOAD` circuit, it only constrains the stack pops, state transition, and lookups to
retrieve the additional information such as tx id, call data offset, etc.
Then the gadget transits to an internal state called `CopyToWord`, which can loop itself for
copying data to the memory until `length == 32` or there are no more bytes to read from the call_data.

## Constraints

1. opId = 0x37
2. State transition:
   - rw_counter
     - +4 for root calls (1 stack read, 1 stack write, 2 call context read)
     - +4 for root calls (1 stack read, 1 stack write, 2 call context read)
   - pc + 1
   - gas + 3 
3. Lookups: 3 (root calls) or 4 (internal calls)
   - `call_data_offset` is at the top of the stack for prev state.
   - `RLC(32 calldata bytes) is at the top of the stack` for next state.
   - `tx_id` is in the rw table (call context)
   - for root calls (`is_root = 1`):
     - `call_data_offset` is in the tx table
   - for internal calls (`is_root = 0`):
     - `call_data_offset` is in the rw table (call context)

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/calldataload.py`.
