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

1. constrain `mStart`, `mSize` pop from stack
2. constrain contract address in CallContext & TxLog
3. constrain call context is not static call
4. constrain topics pop from stack and add into TxLog topic field, topic count is correct
5. constrain memory data \[`mStart`, `mStart` + `mSize`\], copied to tx log data field,
   it takes use of one or more `CopyToLog` inner gadgets as one `CopyToLog` gadget can only handle fixed
   amount of bytes.

## Constraints

1. opId = 0xA0...0xA4

2. State transition:

   - gc :  
   when  is_persistent = false, 
    gc + ( 2 + `N`  stack reads + 3 callcontext reads +  `mSize` memory reads)   
   when  is_persistent = true, 
    gc + ( 2 + `N`  stack reads + 3 callcontext reads +  `mSize` memory reads) + (`N` + 1  + `mSize`) log lookups:
   
   - stack_pointer + 2 + `N`
   - pc + 1
   - reversible_write_counter + 1:
   - log_index + 1
   - memory size to expansion
   - reversible_write_counter + 1
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
