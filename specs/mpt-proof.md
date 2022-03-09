# Merkle Patricia Trie (MPT) Proof

MPT circuit checks that the modification of the trie state happened correctly.

Let's assume there are two proofs (as returned by `eth getProof`):

- A proof that there exists value `val1` at key `key1` for the trie with root `root1`.
- A proof that there exists value `val2` at key `key1` for the trie with root `root2`.

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

- `s_rlp1`
- `s_rlp2`
- `s_advices` (32 columns)
- `c_rlp1`
- `c_rlp2`
- `c_advices` (32 columns)

### Branch

Branch comprises 19 rows:

- 1 init row with some RLP specific data and some selectors
- 16 node rows
- 2 extension node rows

| Row title           | Row example                                                       |
| --------------------- | ------------------------------------------------------------------ |
| Branch init            | `0, 1, 0, 1, 249, 2, 17, 249, 2, 17, 13`                                     |
| Node 0              | `0, 160, 215, 178, 43, ..., 0, 160, 215, 178,...`                                      |
| Node 1              | `0, 160, 195, 189, 38, ..., 0, 160, 195, 19, 38,...`                                      |
| Node 2 (empty)              | `0, 0, 128, 0, 0, ..., 0, 0, 128, 0, 0,...`                                      |
| ...              | ...                                      |
| Node 15              | `0, 160, 22, 99, 129, ..., 0, 160, 22, 99, 129,...`                                      |
| Extension row S              | `228, 130, 0, 149, 0,..., 0, 160, 57, 70,...`                                      |
| Extension row C              | `0, 0, 5, 0, ...,0, 160, 57, 70,... 0`                                      |

![branch](./img/branch.png)

In the picture, the last two rows are all zeros because this is a regular branch,
not an extension node.

`s_advices/c_advices` present the hash of a branch child.
We need `s_advices/c_advices` for two things:

- to compute the overall branch RLC (to be able to check the hash of a branch)
- to check whether `s_advices/c_advices` (at `is_modified` position)
  present the hash of the next element in a proof

Hash lookup looks like (for example for branch S):

```
lookup(S branch RLC, S branch length, s_advices RLC at the is_modified position in parent branch)
```

TODO: instead of 32 columns for `*_advices`, use only the RLC of `*_advices`.
To integrate `*_advices` RLC into the computation of the whole branch RLC, we
just need to compute `mult * *_advices_RLC` and add this to the current RLC value.

The layout then be simply:
`s_rlp1, s_rlp2, s_child_rlc, c_rlp1, c_rlp2, c_child_rlc`

#### Branch init row

The first two columns specify whether S branch has two or three RLP meta bytes
(these bytes specify the length of the stream):

- `1, 0` means two RLP meta bytes
- `0, 1` means three RLP meta bytes

For example, a branch with two RLP meta bytes starts like:
`248, 81, 128, 128,... `
This means there are 81 bytes from position two onward in the branch RLP stream.

To check whether the length of the stream correspond to the length specified
with the RLP meta bytes, we use column 0. In each row we subtract the number
of bytes in a row. In the last row we checked whether the value is 0.

Note that branch node row can either have 33 bytes or 1 byte. 1 byte occurs
when the node is empty, in this case only the value 128 appears, which is stored
in column 2.

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

The first columns of S and C proof (`s_rlp1` and `c_rlp1`) in branch node rows are
used to check the RLP stream length.

The second columns (`s_rlp2` and `c_rlp2`) are for RLP encoding of the length
of the substream.
For non-empty rows, it is always 160, because this denotes the length of the
substream which is 32 (= 160 - 128). The substream in this case is hash of a
node.

When there is an empty node, the column looks like:
`0, 0, 128, 0, ..., 0`.

Empty node in a RLP stream is denoted only by one byte - value 128.
MPT circuit uses padding with 0s to simplify the comparison
between S and C branch. This way, the branch nodes are aligned horizontally
for both proofs.

For example, when a value is stored at a key that
hasn't been used yet, we will get an empty node in S branch and non-empty node
in C branch. We need to compare whether this change corresponds to the
key (key determines the index of the node in branch where change occurs).

#### Constraints

##### Constraint: hash of the branch is in the parent branch

`is_modified` selector denotes the position in branch which corresponds to the key
(the branch child where the change occurs).

The whole branch needs to be hashed and the result needs to be checked
to be in the parent branch. This is checked in `BranchHashInParentChip`
using a lookup which takes as an input:

- Random Linear Combination (RLC) of the branch
- parent branch `s_advices/c_advices` RLC at `is_modified` position

Currently, instead of `s_advices/c_advices` RLC, four columns (bytes into words)
are used: `s_keccak/c_keccak` (to be fixed).

Hash lookup looks like (for S):
`lookup(S branch RLC, S branch length, s_advices RLC)`.

To simplify the constraints, the modified node RLC is stored in each
branch node. This is to enable rotations back to access the RLC of the modified node.
Thus, for example, when checking the branch hash to be in a parent branch,
we can rotate back to the last row in the parent branch and use the value from this
row for the lookup.

Let's see an example.
Let's say we have a branch where `modified_node = 1`. For clarity, let's
denote `s_rlp1, s_rlp2, c_rlp1, c_rlp2` simply with `_`.

```
_, _, b0_s_child0_rlc, _, _, b0_c_child0_rlc
_, _, b0_s_child1_rlc, _, _, b0_c_child1_rlc
...
_, _, b0_s_child15_rlc, _, _, b0_c_child15_rlc
```

Let's say the next element in a proof is another branch:

```
_, _, b1_s_child0_rlc, _, _, b1_c_child0_rlc
_, _, b1_s_child1_rlc, _, _, b1_c_child1_rlc
...
_, _, b1_s_child15_rlc, _, _, b1_c_child15_rlc
```

The hash of this second branch is in the parent branch at position 1.
Let `b1_s` be the RLC of S part of this second branch and
`b1_c` be the RLC of C part of this second branch.
Then:

```
hash(b1_s) = b0_s_child1_rlc
hash(b1_c) = b0_c_child1_rlc
```

Hash lookup like is needed (for S):
`lookup(b1_s, len(b1_s), b0_s_child1_rlc)`

We need a rotation to access `b0_s_child1_rlc`, but we cannot fix the rotation
as the `modified_node` can be any value between 0 and 15 - any of the following
values can appear to be needed: ` b0_s_child0_rlc, b0_s_child1_rlc, ..., b0_s_child15_rlc`.

For this reason there are two additional columns in all 16 branch children rows
that specify the `modified_node` RLC: `modified_node_s_rlc` and `modified_node_c_rlc`.

```
_, _, b0_s_child0_rlc, _, _, b0_c_child0_rlc, b0_modified_node_s_rlc, b0_modified_node_c_rlc
_, _, b0_s_child1_rlc, _, _, b0_c_child1_rlc, b0_modified_node_s_rlc, b0_modified_node_c_rlc
...
_, _, b0_s_child15_rlc, _, _, b0_c_child15_rlc, b0_modified_node_s_rlc, b0_modified_node_c_rlc
```

Now, we can rotate back to any of the branch children rows of `b0` to
access the RLC of the modified node.

Note: currently, the implementation uses `s_keccak/c_keccak` columns
instead of `modified_node_s_rlc` and `modified_node_c_rlc`.

##### Constraints: node hash in branch rows

We need to make sure `modified_node_s_rlc` and `modified_node_c_rlc`
is the same in all branch children rows.

```
modified_node_s_rlc_cur = modified_node_s_rlc_prev
modified_node_c_rlc_cur = modified_node_c_rlc_prev
```

##### Constraint: no change except at is_modified position

In all branch rows, except at `is_modified` position, it needs to hold:

```
s_advices = c_advices
```

### Extension node rows

Extension node can be viewed as a special branch. It contains a regular branch
with the addition of a key extension. Key extension is set of nibbles (most
often only one or two nibbles) that "extend" the path to the branch.

The extension node element in proof (returned by `eth getProof`) contains
the information about nibbles and the hash of the underlying branch.

For example, the proof element of an extension node looks like:

`228,130,0,149,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249`

130 means there are 2 (130 - 128) bytes compressing the nibbles.
These two bytes are
`0, 149`.
The two nibbles compressed are 9 and 5 (149 = 9 * 16 + 5).

The bytes after 160 present a hash of the underlying branch.

MPT layout uses `s_rlp1`, `s_rlp2`, and `s_advices` for RLP meta bytes and nibbles,
while `c_advices` are used for branch hash (`c_rlp2` stores 160 - denoting the number
of hash bytes).

There are two extension node rows - one for S proof, one for C proof.
However, the extension key (nibbles) is the same for both proofs, we don't need
to double this information.
For this reason, in C row, we don't put key into `s_rlp1`, `s_rlp2`, and `s_advices`,
we just put hash of C extension node underlying branch in `c_advices`.

However, in C row, we store additional witness for nibbles (because nibbles are
given compressed in bytes) into `s_rlp1`, `s_rlp2`, and `s_advices`.

For example:
`0, 0, 5, 0, 0, ...`

Here, 5 presents the second nibbles of 149 (see above).
Having the second nibble simplifies the computation of the first nibble.

Thus, the two extension rows look like:

```
228,130,0,149, 0, ..., 0, 160, S underlying branch hash
0, 0, 5, 0, ..., 0, 160, C underlying branch hash
```

There is bit of a difference in RLP stream when only one nibble appears.
In this case there is no byte specifying the length of the key extension
(130 in the above case).
For example, in the case below, the nibble is 0 (16 - 16):

`226,16,160,172,105,12...`

In this case special witnesses for nibbles are not needed.

### Storage leaf

There are 5 rows for a storage leaf.
2 rows for S proof, 2 rows for C proof
(it might be optimized to have only one row for a storage leaf).
1 row for cases when a leaf is turned into a branch or extension node.

`228, 159, 55, 204, 40,...`

______________________________________________________________________

`227, 161, 32, 187, 41, ..., 11`
`225, 159, 57, 202, 166, ..., 17`

## Key RLC
