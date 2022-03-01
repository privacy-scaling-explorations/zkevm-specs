# Merkle Patricia Trie (MPT) Proof

MPT circuit checks that the modification of the trie state happened correctly.

Let's assume there are two proofs (as retured by `eth getProof`):
 * A proof that there exists value `val1` at key `key1` for the trie root `root1`.
 * A proof that there exists value `val2` at key `key1` for the trie root `root2`.

The circuit checks the transition from `val1` to `val2` at `key1` that led to the change
of trie root from `root1` to `root2` (the chaining of such proofs is yet to be added).

The proof returned by `eth getProof` looks like (but there are various special cases):
 * State trie branch 0 that contains 16 nodes, one of them being the hash of the branch below (State trie branch 1)
 * State trie branch 1 that contains 16 nodes, one of them being the hash of the branch below
 * ...
 * State trie branch n
 * State trie leaf that constains the info about account: nonce, balance, storageRoot, codeHash

 * Storage trie branch 0 that contains 16 nodes, one of them being the hash of the branch below (Storage trie branch 1)
 * Storage trie branch 1 that contains 16 nodes, one of them being the hash of the branch below
 * ...
 * Storage trie branch n
 * Storage trie leaf that constains (part of) key `key1` and value `val1`

Let's for demonstration purposes simplify the proof above to only have two storage trie branches
and no state trie part:
 * Storage trie branch 0 that contains 16 nodes, one of them being the hash of the branch below (Storage trie branch 1)
 * Storage trie branch 1 that contains 16 nodes, one of them being the hash of the branch below
 * Storage trie leaf that constains (part of) key `key1` and value `val1`

We split the branch information into 16 rows (one row for each node). The proofs looks like:
 * Branch 0 node 0
 * Branch 0 node 1
 * Branch 0 node 2 (hash of Branch 1)
 * ...
 * Branch 0 node 15
 * Branch 1 node 0
 * Branch 1 node 1 (hash of a leaf)
 * ...
 * Branch 1 node 15
 * Leaf

When `key1` is hashed and converted into hexadecimal value, it is a hexadecimal string of
length 64. The first character specifies under which position of Branch 0 is the node
corresponding to `key1`.
The second character specifies under which position of Branch 1 is the node
corresponding to `key1`. The remaining characters are stored in a leaf.
Let's say the first character is 2 and the second character is 1.
In our case, this means the hash of a leaf is Branch 1 node 1 and hash of Branch 1 is
Branch 0 node 2. 

If we make a change at `key1` from `val1` to `val2` and obtain a proof after this change,
the proof will be different from the first one at Leaf, Branch 1 node 1, and Branch 0 node 2,
other proof elements stay the same.

To check the transition from `root1` to `root2` caused at `key1`, MPT circuit checks that both
proofs are the same except at the nodes that correspond to `key1` path (hexadecimal characters).
In proof 1, the root of Branch 0 needs to be `root1`.
In proof 2, the root of Branch 0 needs to be `root2`.
Furthermore, it needs to be checked that the nodes differ at indexes that
correspond to `key1` path.

To implement the constraints above, the two proofs are put in parallel in MPT rows.
Each branch row contains information of branch node from proof 1 and as well as from proof 2:
 * Branch 0 node 0 before change || Branch 0 node 0 after change
 * Branch 0 node 1 before change || Branch 0 node 1 after change
 * ...
 * Branch 0 node 15 before change || Branch 0 node 15 after change
 * Branch 1 node 0 before change || Branch 1 node 0 after change
 * ...
 * Branch 1 node 15 before change || Branch 1 node 15 after change
 * Leaf (before change)
 * Leaf (after change)

## Circuit Layout

The columns are of two types.

### Branch

Branch comprises 19 rows.

| Row title           | Row example                                                       |
| --------------------- | ------------------------------------------------------------------ |
| Branch init            | `0, 1, 0, 1, 249, 2, 17, 249, 2, 17, 13`                                     |
| Node 0              | `0, 160, 215, 178, 43, ..., 0, 160, 215, 178,...`                                      |
| Node 1              | `0, 160, 195, 19, 38, ..., 0, 160, 195, 19, 38,...`                                      |
| ...              | ...                                      |
| Node 15              | `0, 160, 22, 99, 129, ..., 0, 160, 22, 99, 129,...`                                      |
