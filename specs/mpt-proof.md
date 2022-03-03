# Merkle Patricia Trie (MPT) Proof

MPT circuit checks that the modification of the trie state happened correctly.

Let's assume there are two proofs (as retured by `eth getProof`):

- A proof that there exists value `val1` at key `key1` for the trie root `root1`.
- A proof that there exists value `val2` at key `key1` for the trie root `root2`.

The circuit checks the transition from `val1` to `val2` at `key1` that led to the change
of trie root from `root1` to `root2` (the chaining of such proofs is yet to be added).

The proof returned by `eth getProof` looks like (but there are various special cases):

- State trie branch 0 that contains 16 nodes, one of them being the hash of the branch below (State trie branch 1)

- State trie branch 1 that contains 16 nodes, one of them being the hash of the branch below

- ...

- State trie branch n

- State trie leaf that constains the info about account: nonce, balance, storageRoot, codeHash

- Storage trie branch 0 that contains 16 nodes, one of them being the hash of the branch below (Storage trie branch 1)

- Storage trie branch 1 that contains 16 nodes, one of them being the hash of the branch below

- ...

- Storage trie branch n

- Storage trie leaf that constains (part of) key `key1` and value `val1`

Let's for demonstration purposes simplify the proof above to only have two storage trie branches
and no state trie part:

- Storage trie branch 0 that contains 16 nodes, one of them being the hash of the branch below (Storage trie branch 1)
- Storage trie branch 1 that contains 16 nodes, one of them being the hash of the branch below
- Storage trie leaf that constains (part of) key `key1` and value `val1`

We split the branch information into 16 rows (one row for each node). The proofs looks like:

- Branch 0 node 0
- Branch 0 node 1
- Branch 0 node 2 (hash of Branch 1)
- ...
- Branch 0 node 15
- Branch 1 node 0
- Branch 1 node 1 (hash of a leaf)
- ...
- Branch 1 node 15
- Leaf

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

- Branch 0 node 0 before change || Branch 0 node 0 after change
- Branch 0 node 1 before change || Branch 0 node 1 after change
- ...
- Branch 0 node 15 before change || Branch 0 node 15 after change
- Branch 1 node 0 before change || Branch 1 node 0 after change
- ...
- Branch 1 node 15 before change || Branch 1 node 15 after change
- Leaf (before change)
- Leaf (after change)

## Circuit Layout

The two parallel proofs are called S proof and C proof in the MPT circuit layout.

The first 34 columns are for the S proof.
The next 34 columns are for the C proof.
The remaining columns are selectors, for example, for specifying whether the
row is branch node or leaf node.

34 columns presents 2 + 32. 32 columns are used because this is the length
of hash output.
Note that, for example, each branch node is given in a hash format -
it occupies 32 positions.
The first 2 columns are RLP specific as we will see below.

In the codebase, the columns are named:

- s_rlp1
- s_rlp2
- s_advices (32 columns)
- c_rlp1
- c_rlp2
- c_advices (32 columns)

### Branch

Branch comprises 19 rows:

- 1 init row with some RLP specific data and some selectors
- 16 node rows
- 2 extension node rows

| Row title           | Row example                                                       |
| --------------------- | ------------------------------------------------------------------ |
| Branch init            | `0, 1, 0, 1, 249, 2, 17, 249, 2, 17, 13`                                     |
| Node 0              | `0, 160, 215, 178, 43, ..., 0, 160, 215, 178,...`                                      |
| Node 1              | `0, 160, 195, 19, 38, ..., 0, 160, 195, 19, 38,...`                                      |
| Node 2 (empty)              | `0, 0, 128, 0, 0, ..., 0, 0, 128, 0, 0,...`                                      |
| ...              | ...                                      |
| Node 15              | `0, 160, 22, 99, 129, ..., 0, 160, 22, 99, 129,...`                                      |
| Extension row S              | `228, 160, 22, 99, 129, ..., 0, 160, 22, 99, 129,...`                                      |

#### Branch init row

The first two columns specify whether S branch has two or three RLP meta bytes
(these bytes specify the length of the stream):

- `1, 0` means two RLP meta bytes
- `0, 1` means three RLP meta bytes

For example, a branch with two RLP meta bytes starts like:
`248, 81, 128, 128,... `
This means there are 81 bytes from position two onward.

To check whether the length of the stream correspond to the length specified
with the RLP meta bytes, we use column 0. In each row we subtract the number
of bytes in a row. In the last row we checked whether the value is 0.

Note that branch node row can have either 33 bytes or 1 byte. 1 byte occurs
when the node is empty, in this case only the value 128 appears, which is stored
in position 2 in MPT circuit layout.

For example, a branch with three RLP meta bytes starts like:
`249, 1, 81, 128, 16, ... `
This means there are 1 * 256 + 81 bytes from position three onward.

Summary:

- cols 0 and 1: whether branch S has 2 or 3 RLP meta data bytes
- cols 2 and 3: whether branch C has 2 or 3 RLP meta data bytes
- cols 4 and 5: the actual branch S RLP meta data bytes
- col 6: the actual branch S RLP meta data byte (if there are 3 RLP meta data bytes in branch S)
- cols 7 and 8: branch C RLP meta data bytes
- col 9: the actual branch C RLP meta data byte (if there are 3 RLP meta data bytes in branch C)

TODO: selectors

#### Branch node rows

Each branch node row starts with 34 S proof columns and 34 C proof columns.

Example 34 S columns:

`0, 160, 215, 178, 43, ..., 23`

The first column in branch node rows is used for checking the RLP stream
length.

The second column is RLP encoding of the length of the substream.
It is always 160, because this denotes the length of the
substream which is 32 (= 160 - 128). The substream in this case is hash of a
node.

When there is an empty node, the columns look like:
`0, 0, 128, 0, ..., 0`

Empty node in a RLP stream is denoted only by one byte - value 128.
MPT circuit uses this kind of padding with 0s to simplify the comparison
between S and C branch. For example, when a value is stored at a key that
hasn't been used yet, we will get empty node in S branch and non-empty node
in C branch. We need to compare whether this change corresponds to the
key (key determines the index of the node in branch where change occurs).

#### Extension node rows

Extension node can be viewed as a special branch. It contains a regular branch
with the addition of a key extension. Key extension is a couple of nibbles (most
often only one or two nibbles) that "extend" the path to the branch.

The extension node element in proof contains the information about nibbles
and the hash of the underlying branch.

For example, the proof element (returned by `eth getProof`) of
an extension node looks like:

`228,130,0,149,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249`

130 means there are 2 (130 - 128) bytes compressing the nibbles.
These two bytes are
`0, 149`.
The two nibbles compressed are 9 and 5 (149 = 9 * 16 + 5).

The bytes after 160 present a hash of the underlying branch.

MPT layout uses s_rlp1, s_rlp2, and s_advices for RLP meta bytes and nibbles,
while c_advices are used for branch hash (c_rlp2 stores 160 - denoting the number
of hash bytes).

There are two extension node rows - one for S proof, one for C proof.
However, the nibbles information is the same for both proofs.
For this reason, in C row, we store some additional witness for nibbles (because
the nibbles are actually given compressed in bytes).

`226,16,160,172,105,12...`

`228, 130, 0, 187, 0, ...`

`0, 0, 11, 0, 0, ...`

### Storage leaf

There are 5 rows for a storage leaf.
2 rows for S proof, 2 rows for C proof
(it might be optimized to have only one row for a storage leaf).
1 row for cases when a leaf is turned into a branch or extension node.

`227, 161, 32, 187, 41, ..., 11`

`225, 159, 57, 202, 166, ..., 17`

## Key RLC
