# Log op codes

## Procedure

there are five log related op codes of evm as below:

| id  | name | comment |
| --- | -----| ------- |
| A0  | LOG0 | Append log record with no topics    |
| A1  | LOG1 | Append log record with one topic    |
| A2  | LOG2 | Append log record with two topics   |
| A3  | LOG3 | Append log record with three topics |
| A4  | LOG4 | Append log record with four topics  |

denote `LOGN` where `N` in `[0,4]` meaning topic count.

## EVM behavior

1. LogN first pops two elements `mStart`, `mSize` from stack, then
   pops `N` topics from stack.
2. Copy memory data from `mStart` address with `mSize` length
3. Construct log entry and append to log collections of state

## Circuit behavior

Because the `msize` is dynamic, it requires multiple step slots to fully verify the `CALLDATACOPY`.
In the `Log` circuit, it only constrains the stack pops, state transition, and lookups to
retrieve the additional information such as contract address, `is_static`, etc.
Then the gadget transits to an internal state called `CopyToLog`, which can loop itself for
copying memory data to the RW log entries.

## Constraints

1. opId = 0xA0...0xA4

2. State transition:

   - gc + 5( 2 stack reads + 2 callcontext reads + 1 txlog read) + 2 * `N` + 2 * `mSize`:
   - stack_pointer + 2 + `N`
   - pc + 1
   - state_write_counter + 1:
   - log_index + 1
   - memory size to expansion
   - state_write_counter + 1
   - gas - dynamic_gas
     （dynamic_gas = 375 * `N` + 8 * `msize` + memory_expansion_cost）

3. Lookups:

   1. stack:

      - `mStart` and `mSize`are on the top of stack
      - `N` topic items of stack

   2. memory:

      - memory data (dynamic length) come from address `mStart` with `mSize` length

   3. storage:

      - `N` topics lookup in Tx log entry
      - `msize` data lookup in Tx log entry
      - `CalleeAddress` lookup in CallContext
      - `contract_address` lookup in Tx log entry

   4. others: call context is not static call

## Exceptions

1. stack underflow:\
   (1024 - `stack_pointer`) `<` (2 + `N`)
2. out of gas: remaining gas is not enough
3. error call context within `STATICCALL`

## Code

Refer to src/zkevm_specs/evm/execution/log.py
