# EVM Proof

The EVM proof argues the transition of state trie root is valid by verifying all the included transactions in a block have correct execution results.

EVM circuit re-implements EVM again, but in a perspective of verification, which means prover can help provide hints as long as it's not contradict to the result. For example, prover can give hints about the if this call is going to revert or not, or if this opcode encounters an error or not, then EVM circuit verify that execution results indeed meet the case.

The included transactions in a block could be simple ether transfers, contract creations, or contract interactions, and because each transaction has variable execution trace, we can't have fixed circuit layout to verify specific logic in specific region, we instead need a chip to be able to verify all possible logics, and this chip repeats itself to fill the whole circuit.

## Custom Types

We define the following Python custom types for type hinting and readability:

| Name            | Type                    | Description                                                                     |
| --------------- | ----------------------- | ------------------------------------------------------------------------------- |
| `GlobalCounter` | `int`                   | Order of random access to `BusMapping`, which should be in sequence             |
| `BusMapping`    | `List[Tuple[int, ...]]` | List of random read-write access data in sequence with `GlobalCounter` as index |

## Random Accessible Data

In EVM, the interpreter has ability to do any random access to data like account balance, account storage, or stack and memory in current scope, but it's hard EVM circuit to keep tracking these data to ensure their consistency from time to time. So EVM proof has state proof to provide a valid list of random read-write access records indexed by the `GlobalCounter` as a lookup table to do random access at any moment.

We call the list of random read-write access records `BusMapping` because it acts like the bus in computer which transfers data between components. Similarly, read-only data are loaded as a lookup table into circuit for random access.

| Target                                | Index             | Accessible By   | Description                                                        |
| ------------------------------------- | ----------------- | --------------- | ------------------------------------------------------------------ |
| [`Block`](#Block)                     | `{enum}`          | `Read`          | Block constant decided before executing the block                  |
| [`BlockHash`](#BlockHash)             | `{index}`         | `Read`          | Previous 256 block hashes as a encoded word array                  |
| [`AccountNonce`](#AccountNonce)       | `{address}`       | `Read`, `Write` | Account's nonce                                                    |
| [`AccountBalance`](#AccountBalance)   | `{address}`       | `Read`, `Write` | Account's balance                                                  |
| [`AccountCodeHash`](#AccountCodeHash) | `{address}`       | `Read`, `Write` | Account's code hash                                                |
| [`AccountStorage`](#AccountStorage)   | `{address}.{key}` | `Read`, `Write` | Account's storage as a key-value mapping                           |
| [`Code`](#Code)                       | `{hash}.{index}`  | `Read`          | Executed code as a byte array                                      |
| [`Call`](#Call)                       | `{id}.{enum}`     | `Read`          | Call's context decided by caller (includes EOA and internal calls) |
| [`CallCalldata`](#CallCalldata)       | `{id}.{index}`    | `Read`          | Call's calldata as a byte array (only for EOA calls)               |
| [`CallSignature`](#CallSignature)     | `{id}.{index}`    | `Read`          | Call's signature as a byte array (only for EOA calls)              |
| [`CallState`](#CallState)             | `{id}.{enum}`     | `Read`, `Write` | Call's internal state                                              |
| [`CallStateStack`](#CallStateStack)   | `{id}.{index}`    | `Read`, `Write` | Call's stack as a encoded word array                               |
| [`CallStateMemory`](#CallStateMemory) | `{id}.{index}`    | `Read`, `Write` | Call's memory as a byte array                                      |

## Circuit Constraints

The repeated chip has 2 main states, one is call initialization, another is bytecode execution.

**TODO**
