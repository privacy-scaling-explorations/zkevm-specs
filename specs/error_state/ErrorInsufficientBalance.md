# ErrorInsufficientBalance state

## Procedure
### EVM behavior
this type of error only occurs when executing op code is  `Call` `CallCode` ,`Create` or `Create2`.

Pop one EVM word `value` from the stack, then go to `ErrorInsufficientBalance` state when 
caller's balance <  `value`

### Constraints
1. caller's balance <  `value`
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

## Code

Please refer to `src/zkevm_specs/evm/execution/error_insufficient_balance.py`.
