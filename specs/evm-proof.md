# EVM Proof

## Random Accessible Data

| Target                                | Index             | Accessible By   | Description                                           |
| ------------------------------------- | ----------------- | --------------- | ----------------------------------------------------- |
| [`Block`](#Block)                     | `{enum}`          | `Read`          | Block constant decided before executing the block     |
| [`BlockHash`](#BlockHash)             | `{index}`         | `Read`          | Previous 256 block hashes as a encoded word array     |
| [`AccountNonce`](#AccountNonce)       | `{address}`       | `Read`, `Write` | Account's nonce                                       |
| [`AccountBalance`](#AccountBalance)   | `{address}`       | `Read`, `Write` | Account's balance                                     |
| [`AccountCodeHash`](#AccountCodeHash) | `{address}`       | `Read`, `Write` | Account's code hash                                   |
| [`AccountStorage`](#AccountStorage)   | `{address}.{key}` | `Read`, `Write` | Account's storage as a key-value mapping              |
| [`Code`](#Code)                       | `{hash}.{index}`  | `Read`          | Executed code as a byte array                         |
| [`Call`](#Call)                       | `{id}.{enum}`     | `Read`          | Call's context decided by caller                      |
| [`CallCalldata`](#CallCalldata)       | `{id}.{index}`    | `Read`          | Call's calldata as a byte array (only for EOA calls)  |
| [`CallSignature`](#CallSignature)     | `{id}.{index}`    | `Read`          | Call's signature as a byte array (only for EOA calls) |
| [`CallState`](#CallState)             | `{id}.{enum}`     | `Read`, `Write` | Call's internal state                                 |
| [`CallStateStack`](#CallStateStack)   | `{id}.{index}`    | `Read`, `Write` | Call's stack as a encoded word array                  |
| [`CallStateMemory`](#CallStateMemory) | `{id}.{index}`    | `Read`, `Write` | Call's memory as a byte array                         |
