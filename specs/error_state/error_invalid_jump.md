# ErrorOutOfGasConstant state

## Procedure
this type of error maybe occurs when executing op code is JUMP or JUMPI.

### EVM behavior

Pop one EVM word `dest` from the stack, then go to `ErrorInvalidJump` state when 
one of the followings occurs:

-  `dest` is not within code length range
-  `dest` is a not `JUMPDEST` code , or data section of PUSH*

1. If current is a root call, it ends the execution.
2. Otherwise, it restores caller's context and switch to it.

### Constraints
1. .
2. Current call must be failed.
3. If it's a root call, it transits to `EndTx`, and the call's `IsPersistent` must be false
4. if it is not root call, it restores caller's context by reading to `rw_table`, then does step state transition to it.

### Lookups
- 1 Byte code lookup.
- Call Context lookup `CallContextFieldTag.IsPersistent` (Only if Current instruction is root.).

## Code

Please refer to `src/zkevm_specs/evm/execution/oog_constant.py`.
