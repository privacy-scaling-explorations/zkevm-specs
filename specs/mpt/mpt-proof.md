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

This section explains why MPT circuit handles two parallel proofs at the
same time. There is `S` (as `State`) proof which presents the state of the trie
before the modification. And there is `C` (as `Change`) proof which presents the state
of the trie after modification. 

The columns are split into two categories (not to be mixed with two parallel proofs).
There are `2 * (2 + 32)` columns which contain RLP
streams returned by `getProof`. The other columns are selectors (for example which kind of
row we are at).

The value `2 * (2 + 32)` comes from the fact that keccak output is of 32 width.
The additional 2 bytes are for RLP specific bytes which store information like
how long is the substream.
Finally, the multiplier 2 is because we always have two parallel proofs:
before and after the modification.

The struct `MainCols` contains `rlp1`, `rlp2` bytes (2 bytes) and an array `bytes` of length 32.
There is `MainCols` for `S` proof (named `s_main`) and
`MainCols` for `C` proof (named `c_main`).

Branch contains 16 children which are distributed over 16 rows.
We have branch `S` and branch `C`.

Branch rows:
```
Branch S child 0 | Branch C child 0
...
Branch S child 15 | Branch C child 15
```

The branch does not include raw children, it includes only a hash of each children (except
when a child is shorter than 32 bytes, in this case the raw child is part of a branch).

To get some impression how the witness data is distributed over the columns let us observe
the branch layout.
Branch rows look like (you can see there are `2 * (2 + 32)` columns):
```
s_main                     | c_main
rlp1 rlp2 bytes            | rlp1 rlp2 bytes
0    160  hash(S child 0)  | 0    160  hash(C child 0)
...
0    160  hash(S child 15) | 0    160  hash(C child 15)
```

The value 160 is RLP specific and it means that the following RLP string is of length
`32 = 160 - 128`.

Branch can have some empty children, in this case the row looks like:
```
0 0 128 0 ... 0 | 0 0 128 0 ... 0 
```

In case, there is a child of length smaller than 32, its corresponding branch row looks like:
```
0 0 194 32 1 0 ... 0 | 0 0 194 32 1 0 ... 0 
```

The value 194 is RLP specific and it means that the following RLP list is of length
`2 = 194 - 192`.

## Proof type

MPT circuit supports the following proofs:
 - Storage modification
 - Nonce modification
 - Balance modification
 - Codehash proof
 - Account delete modification
 - Non existing account proof
 - Non existing storage proof

There is a struct `ProofTypeCols` that is used to specify the type of a proof:
```
struct ProofTypeCols {
    proof_type: Column<Advice>,
    is_storage_mod: Column<Advice>,
    is_nonce_mod: Column<Advice>,
    is_balance_mod: Column<Advice>,
    is_codehash_mod: Column<Advice>,
    is_account_delete_mod: Column<Advice>,
    is_non_existing_account_proof: Column<Advice>,
    is_non_existing_storage_proof: Column<Advice>,
}
```

Except for the `proof_type`, the fields are boolean to simplify the writing of the constraints.
The MPT lookup uses only the `proof_type` field - one of the following values:

```
NonceMod = 1
BalanceMod = 2
CodeHashMod = 3
NonExistingAccountProof = 4
AccountDeleteMod = 5
StorageMod = 6
NonExistingStorageProof = 7
```

## Constraints for different types of nodes

The constraints are grouped according to different trie node types:
 * Account leaf constraints documentation is in [account-leaf.md](account-leaf.md).
 * Storage leaf constraints documentation is in [storage-leaf.md](storage-leaf.md).
 * Branch constraints documentation is in [branch.md](branch.md).
 * Extension node constraints documentation is in [extension-node.md](extension-node.md).
 * Proof chain constraints documentation is in [proof_chain.md](proof_chain.md).
 * Selector constraints documentation is in [selectors.md](selectors.md).

Some visual presentations of the MPT circuit aspects can be found [here](visual.md).
Explanation about helper methods that are used across different configs can be found
[here](helpers.md).

## Proof chaining

One proof proves one modification. When two or more modifications are to be
proved to be correct, a chaining between proofs is needed.
That means we need to ensure:

```
current S state trie root = previous C state trie root
```

For this reason `not_first_level` selector is used which is set to 0 for the
first rows of the proof. These are either the rows of the first
branch / extension node or the rows of the account leaf (if only one element
in the state trie).

Having `not_first_level` selector we know when the switch happens to a new proof and the constraint
above can be ensured.