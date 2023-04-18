# Merkle Patricia Trie (MPT) Proof

MPT circuit checks that the modification of the trie state happened correctly.

Let us assume there are two proofs (as returned by `eth getProof`):

- A proof that there exists value `val1` at key `key1` for address `addr` in the state trie with root `root1`.
- A proof that there exists value `val2` at key `key1` for address `addr` in the state trie with root `root2`.

The circuit checks the transition from `val1` to `val2` at `key1` that led to the change
of trie root from `root1` to `root2`.

Similarly, MPT circuit can prove that `nonce`, `balance`, or `codehash` has been changed at
a particular address. But also, the circuit can prove that at a particular address no account exists
(`NonExistingAccountProof`), that at particular storage key no value is stored `NonExistingStorageProof`,
or that at a particular address an account has been deleted.

The circuit exposes a table which looks like:

| Address | ProofType               | Key  | ValuePrev     | Value        | RootPrev  | Root  |
| ------- | ----------------------- | ---- | ------------- | ------------ | --------- | ----- |
| $addr   | NonceMod                | 0    | $noncePrev    | $nonceCur    | $rootPrev | $root |
| $addr   | BalanceMod              | 0    | $balancePrev  | $balanceCur  | $rootPrev | $root |
| $addr   | CodeHashMod             | 0    | $codeHashPrev | $codeHashCur | $rootPrev | $root |
| $addr   | NonExistingAccountProof | 0    | 0             | 0            | $root     | $root |
| $addr   | AccountDeleteMod        | 0    | 0             | 0            | $rootPrev | $root |
| $addr   | StorageMod              | $key | $valuePrev    | $value       | $rootPrev | $root |
| $addr   | NonExistingStorageProof | $key | 0             | 0            | $root     | $root |

Note that `StorageMod` proof also supports storage leaf creation and storage leaf deletion,
`NonceMod` also supports account leaf creation with nonce value and the rest of fields set to default, and
`BalanceMod` also supports account leaf creation with balance value and the rest of fields set to default.

The proof returned by `eth getProof` looks like:

```
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": {
    "accountProof": [
      "0xf90211a...0701bc80",
      "0xf90211a...0d832380",
      "0xf90211a...5fb20c80",
      "0xf90211a...0675b80",
      "0xf90151a0...ca08080"
    ],
    "balance": "0x0",
    "codeHash": "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
    "nonce": "0x0",
    "storageHash": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
    "storageProof": [
      {
        "key": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        "proof": [
          "0xf90211a...0701bc80",
          "0xf90211a...0d832380"
        ],
        "value": "0x1"
      }
    ]
  }
}
```

In the above case, the account proof contains five elements.
The first four are branches or extension nodes, the last one is an account leaf.
The hash of the account leaf is checked to
be in the fourth element (at the proper position - depends on the account address).
The hash of the fourth element is checked to be in the third element (at the proper position).
When we arrive to the top, the hash of the first element needs to be the same as trie root.

The storage proof in the above case contains two elements.
The first one is branch or extension node, the second element is a storage leaf.
The hash of the storage leaf is checked to
be in the first element at the proper position (depends on the key).

The hash of the first storage proof element (storage root) needs to be checked
to be in the account leaf of the last account proof element.

## Two parallel proofs

This section explains why the MPT circuit handles two parallel proofs at the
same time. One proof presents the state (might be denoted as `S` or `State`) of the trie
before the modification and the othe presents the state
of the trie after modification (might be denoted as `C` or `Change`).

We do not need to include the whole `C` proof in the witness as 15 out of 16 rows stay the same.
At each trie level, there is only one branch child that has been modified.

## Proof type

MPT circuit supports the following proofs:
 - NonceChanged
 - BalanceChanged
 - CodeHashExists
 - AccountDestructed
 - AccountDoesNotExist
 - StorageChanged
 - StorageDoesNotExist
 
## Constraints for different types of nodes

The constraints are grouped according to different trie node types:
 * Account leaf: [account-leaf.md](account-leaf.md)
 * Storage leaf: [storage-leaf.md](storage-leaf.md)
 * Branch and extension node: [branch.md](branch.md)

Additionally, [there](rlp-gadget.md) is a RLP gadget for RLP constraints as all trie nodes are RLP
encoded. To ensure the initial state is set properly, there is the [start gadget](start.md).

## Proof chaining

One proof proves one modification. When two or more modifications are to be
proved to be correct, a chaining between proofs is needed.
That means we need to ensure:

```
current S state trie root = previous C state trie root
```