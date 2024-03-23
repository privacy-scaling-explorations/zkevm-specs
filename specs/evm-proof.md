# EVM Proof

The EVM proof argues the transition of state trie root is valid by verifying all the included transactions in a block have correct execution results.

EVM circuit re-implements the EVM, but in a perspective of verification, which means the prover can help provide hints as long as it does not contradict the result. For example, the prover can give hints about if this call is going to revert or not, or if this opcode encounters an error or not, then the EVM circuit can verify that execution results is correct.

The included transactions in a block could be simple ether transfers, contract creations, or contract interactions, and because each transaction has variable execution trace, we can't have fixed circuit layout to verify specific logic in specific region, we instead need a chip to be able to verify all possible logics, and this chip repeats itself to fill the whole circuit.

## Custom Types

We define the following Python custom types for type hinting and readability:

| Name            | Type                    | Description                                                                     |
| --------------- | ----------------------- | ------------------------------------------------------------------------------- |
| `GlobalCounter` | `int`                   | Order of random access to `BusMapping`, which should be in sequence             |
| `BusMapping`    | `List[Tuple[int, ...]]` | List of random read-write access data in sequence with `GlobalCounter` as index |

## Random Accessible Data

In EVM, the interpreter has ability to do any random access to data like account balance, account storage, account transient storage or stack and memory in current scope, but it's hard for the EVM circuit to keep tracking these data to ensure their consistency from time to time. So EVM proof has the state proof to provide a valid list of random read-write access records indexed by the `GlobalCounter` as a lookup table to do random access at any moment.

We call the list of random read-write access records `BusMapping` because it acts like the bus in computer which transfers data between components. Similarly, read-only data are loaded as a lookup table into circuit for random access.

| Target                                | Index             | Accessible By   | Description                                                        |
| ------------------------------------- | ----------------- | --------------- | ------------------------------------------------------------------ |
| [`Block`](#Block)                     | `{enum}`          | `Read`          | Block constant decided before executing the block                  |
| [`BlockHash`](#BlockHash)             | `{index}`         | `Read`          | Previous 256 block hashes as an encoded word array                  |
| [`AccountNonce`](#AccountNonce)       | `{address}`       | `Read`, `Write` | Account's nonce                                                    |
| [`AccountBalance`](#AccountBalance)   | `{address}`       | `Read`, `Write` | Account's balance                                                  |
| [`AccountCodeHash`](#AccountCodeHash) | `{address}`       | `Read`, `Write` | Account's code hash                                                |
| [`AccountStorage`](#AccountStorage)   | `{address}.{key}` | `Read`, `Write` | Account's storage as a key-value mapping                           |
| [`AccountTransientStorage`](#AccountTransientStorage)   | `{address}.{key}` | `Read`, `Write` | Account's transient storage as a key-value mapping                           |
| [`Code`](#Code)                       | `{hash}.{index}`  | `Read`          | Executed code as a byte array                                      |
| [`Call`](#Call)                       | `{id}.{enum}`     | `Read`          | Call's context decided by caller (includes EOA and internal calls) |
| [`CallCalldata`](#CallCalldata)       | `{id}.{index}`    | `Read`          | Call's calldata as a byte array (only for EOA calls)               |
| [`CallSignature`](#CallSignature)     | `{id}.{index}`    | `Read`          | Call's signature as a byte array (only for EOA calls)              |
| [`CallState`](#CallState)             | `{id}.{enum}`     | `Read`, `Write` | Call's internal state                                              |
| [`CallStateStack`](#CallStateStack)   | `{id}.{index}`    | `Read`, `Write` | Call's stack as an encoded word array                               |
| [`CallStateMemory`](#CallStateMemory) | `{id}.{index}`    | `Read`, `Write` | Call's memory as a byte array                                      |

## Circuit Constraints

The repeated chip has 2 main states, one is call initialization, another is bytecode execution.

**TODO**

## Account non-existence

The following opcodes contain special cases for non-existing accounts:
- BALANCE
- EXTCODEHASH
- EXTCODECOPY
- EXTCODESIZE
- CALL
- CALLCODE
- DELEGATECALL
- STATICCALL

The rest of the opcodes only deal with accounts that are known to exist (by previous conditions).

We encode the state of existence of an account with its value of the
`code_hash` in the `rw_table` (managed by the State Circuit): `code_hash = 0`
means that the account doesn't exist, and `code_hash != 0` means that the
account exists.  We can guarantee this fact with the following properties:
- Every time an account is created, the `code_hash` is set from zero to a
  non-zero value.
    - By the read consistency guaranteed by the State Circuit, we know that if a
      `code_hash` is non-zero, the account must exist (because it has been created
      previously)
- A `code_hash` read with value 0 is translated to a non-existence account
  proof in the MPT (via the state circuit).
    - From this we know that if a `code_hash` is read as zero, the account
      doesn't exist.
- There are no other valid transitions of `code_hash`.  In summary, the valid
  transitions are: `0->0`, and `0->H` (where H != 0).  Note that we're not
  considering account destruction for now.

Since only `code_hash` encodes account existence, we must be careful to never
read (lookup) another account property unless we have checked that the account
exists.  This is because the RwTable in the State Circuit has all the entries
sorted by [Tag, FieldTag], so `CodeHash`, `Nonce` and `Balance` are treated
independently, which means that a lookup to `Nonce` or `Balance` could succeed
on a non-existing account if the account is created afterwards.  For this
reason we must guarantee that:
- A `Nonce` and `Balance` lookup to an account must only be performed if we
  have previously verified that the account exists by reading its `CodeHash`
  and checking it to be non-zero.  This check can be done in the same step (for
  opcodes that can deal with non-existing accounts), or in a previous step (as
  a precondition, for opcodes that work with the caller account).

