# ErrorReturnDataOutOfBound state

## Procedure
this type of error only occurs when executing op code is `RETURNDATACOPY`.

### EVM behavior
when run `RETURNDATACOPY` op code, read stack for three fields: `memOffset`,
`dataOffset`, `length`. then check if overflow as following order:  
1. check `dataOffset`is u64 overflow, stop if yes.
2. calculate `end` =  `dataOffset` + `length`.  
3. check `end`is u64 overflow, stop if yes.
4. check `end`> last callee's return data length, stop if yes.

### Constraints
1. op code must be `RETURNDATACOPY`
2. stack reads constraint for `memOffset`,
`dataOffset`, `length`.
3. constrain `dataOffset` is overflow, if not, constrain `end` is overflow
4. if above both not overflow, constrain `end`> last callee's return data length
5. common error constraints: 
  - current call must be failed. 
  - constrain rw_counter_end_of_reversion
  - If it's a root call, it transits to `EndTx`
  - if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code
    TODO: add it after circuit merged