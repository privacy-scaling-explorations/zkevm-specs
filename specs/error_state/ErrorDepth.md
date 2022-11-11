# ErrorDepth state

## Procedure
For CALL-family codes this type of error occurs when causing a callstack overflow.

### EVM behavior
1. Fail the call attempt resulting in pushing `0` into stack
2. Continue the execution of current context

### Constraints
1. Current opcode must be CALL-family codes.
2. `depth == 1025`.
3. The next step with `0` on stack top.

### Lookups
- 1 Call Context lookup `CallContextFieldTag.Depth`
- 1 Stack push lookup

## Code

Please refer to `src/zkevm_specs/evm/execution/error_depth.py`.

### Solidity Code to trigger ErrorDepth
```solidity
PUSH32 0x7f602060006000376000600060206000600060003561ffff5a03f10000000000
PUSH1 0x0
MSTORE
PUSH32 0x0060005260206000F30000000000000000000000000000000000000000000000
PUSH1 0x20
MSTORE

PUSH1 0x40
PUSH1 0x0
PUSH1 0x0
CREATE

DUP1
PUSH1 0x40
MSTORE

PUSH1 0x0 // retSize
PUSH1 0x0 // retOffset
PUSH1 0x20 // argSize
PUSH1 0x40 // argOffset
PUSH1 0x0 // Value
DUP6
PUSH2 0xFF
GAS
SUB
CALL
```