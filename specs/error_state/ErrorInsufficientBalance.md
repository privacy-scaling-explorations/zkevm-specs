# ErrorInsufficientBalance state

## Procedure
### EVM behavior
this type of error only occurs when executing op code is  `Call` `CallCode` ,`Create` or `Create2`.
For `Call` `CallCode`, it will pop 7 stack elements , and the third is transfer `value` within the call.
when caller's balance <  `value`, then go to `ErrorInsufficientBalance` state. for this kind of error, the failed
call result was pushed into stack, continue to execute next step.

### circuit behavior
1.  pop 7 stack elements, even though the other six elements not closely relevant to this error
state constraints, but in order to be accordance with evm trace, also need to handle them here for stack pointer
transition, which impact next step's stack status.

2. lookup current callee address and its balance, then ensure balance <  `value`

## Code

Please refer to `src/zkevm_specs/evm/execution/error_insufficient_balance.py`.
