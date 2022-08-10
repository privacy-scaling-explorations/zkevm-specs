# Merkle Patricia Trie (MPT) Proof

MPT circuit checks that the modification of the trie state happened correctly.

Let us assume there are two proofs (as returned by `eth getProof`):

- A proof that there exists value `val1` at key `key1` for address `addr` in the state trie with root `root1`.
- A proof that there exists value `val2` at key `key1` for address `addr` in the state trie with root `root2`.

The circuit checks the transition from `val1` to `val2` at `key1` that led to the change
of trie root from `root1` to `root2` (the chaining of such proofs is yet to be added).

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

In the above case account proof contains five elements.
The first four are branches / extension nodes, the last one is account leaf.
The hash of the account leaf is checked to
be in the fourth element (at the proper position - depends on the account address).
The hash of the fourth element is checked to be in the third element (at the proper position) ...

The storage proof in the above case contains two elements.
The first one is branch or extension node, the second element is storage leaf.
The hash of storage leaf is checked to
be in the first element at the proper position (depends on the key).

The hash of the first storage proof element (storage root) needs to be checked
to be in the account leaf of the last account proof element.

## Two parallel proofs

This section gives a bit of intuition why MPT circuit handles two parallel proofs at the
same time. Namely, there is `S` (as `State`) proof which presents the state of the trie
before the modification. And there is `C` (as `Change`) proof which presents the state
of the trie after modification. 

The columns are split into two categories (not to be mixed with two parallel proofs).
There are `2 * (2 + 32)` columns which contain RLP
streams returned by `getProof`. The other columns are selectors (for example which kind of
row we are at).

The value `2 * (2 + 32)` is motivated by the fact that keccak output is of 32 width.
The additional 2 bytes are for RLP specific bytes which store information like
how long is the substream.
Finally, the multiplier 2 is because we always have two parallel proofs:
before and after modification.

The struct `MainCols` contains `rlp1`, `rlp2` bytes (2 bytes) and an array `bytes` of length 32.
There is `MainCols` for `S` proof (named `s_main`) and
`MainCols` for `C` proof (named `c_main`).

Let us observe a branch. It contains 16 children which are distributed over 16 rows.
We have branch `S` and branch `C`.

Branch rows:
```
Branch S child 0 | Branch C child 0
...
Branch S child 15 | Branch C child 15
```

The branch does not include raw children, it includes only a hash of each children (except
when a child is shorter than 32 bytes, in this case the raw child is included in a branch).

Branch rows (you can see there are `2 * (2 + 32)` columns):
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
 - Account delete
 - Non existing account

There is a struct `ProofTypeCols` that is to be used to specify the type of a proof:
```
struct ProofTypeCols {
    is_storage_mod: Column<Advice>,
    is_nonce_mod: Column<Advice>,
    is_balance_mod: Column<Advice>,
    is_account_delete_mod: Column<Advice>,
    is_non_existing_account_proof: Column<Advice>,
}
```

The columns in the struct falls into selectors category (as opposed to `MainCols` columns).
`SelectorsChip` ensures there is exactly one type of proof selected.

## Account leaf

Account leaf constraints documentation is in [account-leaf.md](account-leaf.md).