# ErrorWriteProtection state

## Procedure
there are some op codes which modify state. there are `[SSTORE, CREATE, CREATE2, 
CALL, SELFDESTRUCT, LOG0, LOG1, LOG2, LOG3, LOG4]`
when execution call context is read only (static call), these op codes running will encounter
write protection error.
### EVM behavior
in above op codes which modify state, `CALL` is somewhat special. for non call op codes(SSTORE, CREATE, etc)
first check if running in read only call context, if yes, throw write protection error.
for `CALL` op code, it will also check `value` is not zero. only both non zero value & read only call context, then
throw write protection error.

### Constraints
1. constrain this error happens in one of op codes `[SSTORE, CREATE, CREATE2, 
CALL, SELFDESTRUCT, LOG0, LOG1, LOG2, LOG3, LOG4]`
2. current call context must be readonly & internal call(since requires at least one `staticcall` earlier).
3. for `CALL` op code, do stack read & check `value` is not zero.
4. common error steps constraints:
  - current call must be failed.
  - rw_counter_end_of_reversion constraint
  - it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code
    TODO: after circuit merge!