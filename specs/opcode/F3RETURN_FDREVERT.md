# RETURN and REVERT opcodes

## Procedure

### EVM behavior

The `RETURN` opcode ends the call in success. The `REVERT` opcode ends the call
in failure and reverts state changes made in the call and its sub-calls. Both
copy a chunk of memory from the call to its caller.

Depending on if the call is a root call and/or is a create call, these opcodes
will do one or more of the following:

**A** - returns the specified memory chunk as deployment code, if the opcode is
*RETURN, `is_create` is true, and the chunk is non-empty.

**B** - end the execution, if `is_root`.

**C** - restores caller's context and switch to it, if `not is_root`.

**D** - returns the specified memory chunk to the caller, if `not is_create`,
*`not is_root`, and the chunk is non-empty.

**E** - revert state changes made in the call and its sub-calls, if the opcode
is REVERT.

### Circuit behavior

The circuit first checks that `is_success` in call context is matches the
opcode, `True` for RETURN and `False` for REVERT.

We define source memory chunk by the arguments `offset` and `length`, obtained
from the stack via 2 lookups.

If `length > 0`, perform memory expansion to `offset + length`.

For each of the lettered cases:
**A** - it updates the code hash of the address and copy the source memory chunk
to the bytecode identified by its hash, using a lookup to the copy circuit with
the following parameters:
```
{
  src_id: callee.call_id,
  src_tag: Memory,
  src_addr: return_offset,
  src_addr_end: return_offset + return_length,
  length: return_length,
  dst_id: code_hash,
  dst_tag: Bytecode,
  dst_addr: 0,
  rw_counter: callee.rw_counter,
  rwc_inc: return_length,
}
```
If `length` is 0, do not perform the copy circuit lookup.

**B** - it transitions to `EndTx` with `is_persistent` being `True` or `False`
if the opcode is RETURN or REVERT, respectively.

**C** - it restores the caller's context by reading to `rw_table`, and then does
*a step state transition back to the caller.

**D** - if it isn't a root call and isn't an `is_create` call context, it copies
*the source memory chunk to the caller's memory defined by the `*CALL*`
*arguments `retOffset`, `retLength`, using a lookup to the copy circuit with the
*following parameters:
```
{
  src_id: callee.call_id,
  src_tag: Memory,
  src_addr: return_offset`,
  src_addr_end: return_offset + return_length,
  length: min(return_length, call_context[ReturnDataLength, callee_id]),
  dst_id: caller.call_id,
  dst_tag: Memory,
  dst_addr: call_context[ReturnDataOffset, callee_id],
  rw_counter: callee.rw_counter,
  rwc_inc: 2 * min(return_length, call_context[ReturnDataLength, callee_id]),
}
```
If `min(return_length, call_context[ReturnDataLength, callee_id])` is zero, it
does not perform the copy circuit lookup.

**E** - The rw lookups needed for reverting the state changes are handled by the
*`ReversionInfo` used when making reversible writes, so we do not need to make
*them in this gadget. However, the step state transition of the `rw_counter`
*will be increased by `instruction.curr.reversible_write_counter` to account for
*making the reversions.

### Gas cost

The only gas cost incurred by `RETURN` and `REVERT` is the one that comes from
the memory expansion related to the returned memory chunk. If there's no memory
expansion, the gas cost is 0.

## Constraints

1. opId - 0xF3
2. State transition:
    - rwc and `rw_table` lookups:
        - Fixed: 1 (`call_context` lookup) + 2 (stack lookup)
        - If case A: + `copy_length` (copy circuit)
        - If case B: + 1 (`call_context` lookup)
        - If case C: + 12 (`rw_table` lookups from transition to restored context)
        - If case D: + 2 (`call_context` lookup) + 2 * `copy_length` (copy circuit)
        - If case E: `reversible_write_counter` `rw_table` lookups for reversion
    - gas left: `caller_gas_left - return_gas_cost`
    - restore context to caller context
3. Lookups (outside of `rw_table`)
    - If case **A**: `copy_circuit` lookup for memory to bytecode copy
    - If case **D**: `copy_circuit` lookup for memory to memory copy

## Exceptions

1. stack underflow: `1023 <= stack_pointer <= 1024`
2. out of gas: remaining gas is not enough

## Code

Please refer to `src/zkevm_specs/evm/execution/return_revert.py`.
