# Merkle Patricia Trie (MPT) Proof

MPT circuit checks that the modification of the trie state happened correctly.

Let's assume there are two proofs (as returned by `eth getProof`):

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

We split the branch information into 16 rows (one row for each node). The proof looks like:

<p align="center">
  <img src="./img/proof.png?raw=true" width="25%">
</p>

A key is hashed and converted into hexadecimal value - it becomes a hexadecimal string of
length 64.
Let's say we have a leaf:

```
key = [10,6,3,5,7,0,1,2,12,1,10,3,10,14,0,10,1,7,13,3,0,4,12,9,9,2,0,3,1,0,3,8,2,13,9,6,8,14,11,12,12,4,11,1,7,7,1,15,4,1,12,6,11,3,0,4,2,0,5,11,5,7,0,16]
val = [2]
```

In a proof, key is put in the
[compact form](https://github.com/ethereum/go-ethereum/blob/master/trie/hasher.go#L110)
It becomes:

```
[58,99,87,1,44,26,58,224,161,125,48,76,153,32,49,3,130,217,104,235,204,75,23,113,244,28,107,48,66,5,181,112]
```

Then the leaf is
[RLP encoded](https://github.com/ethereum/go-ethereum/blob/master/trie/hasher.go#L157)
It becomes:

```
[226,160,58,99,87,1,44,26,58,224,161,125,48,76,153,32,49,3,130,217,104,235,204,75,23,113,244,28,107,48,66,5,181,112,2]
```

Note that the RLP contains the key and the value (the last byte). In such a format, a storage
leaf appears in the MPT proof.

The leaf RLP is hashed and it appears in the parent branch as:

```
[32,34,39,131,73,65,47,37,211,142,206,231,172,16,11,203,33,107,30,7,213,226,2,174,55,216,4,117,220,10,186,68]
```

Key nibbles specify the positions in branches / extension nodes.
The first nibble specifies under which position of Branch 0 is the node
corresponding to `key1`.
The second nibble specifies under which position of Branch 1 is the node
corresponding to `key1`. The remaining nibbles are stored in a storage leaf
(in a compact form).

In account proof, address is analogous to key in storage proof.

<p align="center">
  <img src="./img/address_key.png?raw=true" width="50%">
</p>

In the above case, we have three branches / extension nodes in the account proof.
Let's say `addr` turns into nibbles `3 b a ...` That would mean the position (named `modified_node`) of the underlying proof element is:

- 3 in Branch 0
- 11 in Branch 1
- 10 in Branch 2

For the storage part, we have two branches / extension nodes.
Let's say `key1` turns into nibbles `a 2 ...` That would mean the position (named `modified_node`) of the underlying storage leaf is:

- 10 in Branch 0
- 2 in Branch 1

If we make a change at `key1` from `val1` to `val2` and obtain a proof after this change,
the proof will be different from the first only at `modified_node` positions.

To check the transition from `root1` to `root2` caused at `key1`, MPT circuit checks that both
proofs are the same except at the nodes that correspond to `key1` path
(hexadecimal characters presenting `modified_node`).

In proof 1, the root of account Branch 0 needs to be `root1`.
In proof 2, the root of account Branch 0 needs to be `root2`.
Also, it needs to be checked that the nodes differ only at indexes that
correspond to `key1` path.

To implement the constraints above, the two proofs are put in parallel in MPT rows.
Each branch row contains information of branch node from proof 1 and as well as from proof 2:

<p align="center">
  <img src="./img/mpt.png?raw=true" width="65%">
</p>

Proof 1 is on the left side, proof 2 is on the right side.

## Branch / extension node layout

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

Branch (the two extension node rows are empty):

<p align="center">
  <img src="./img/branch_diagram.png?raw=true" width="50%">
</p>

Extension node:

<p align="center">
  <img src="./img/extension_node.png?raw=true" width="50%">
</p>

Boolean selectors `is_branch_init`, `is_branch_child`, `is_last_branch_child`,
`is_modified` to trigger the constraints only when necessary.
Two examples:

- checking that branch RLC is computed properly is done in the last branch row (`is_last_branch_child`)
- S and C children are checked to be the same in all rows except at `is_modified`

There are two other columns that make sure the branch rows apply to the prescribed layout:
`node_index` and `modified_node`.

`node_index` is checked to be running monotonously from 0 to 15.
This way it is ensured that branch layout really has 16 branch children rows.

`modified_node` specifies the index at which the storage modification in this branch occured.
`modified_node` is checked to be the same in all branch children rows - having this value
available in all rows simplifies the constraints for checking that `is_modified` is true
only when `node_index - modified_node = 0`. Having `modified_node` available only in one row,
it would be difficult to write a constraint for `node_index - modified_node = 0` for all
16 rows.

`is_last_branch_child` is checked to be in the row with `node_index` = 15.
`is_branch_child` is checked to follow either `is_branch_init` or `is_branch_child`.
After `is_branch_init` it is checked to be `is_branch_child = 1`.
After `is_branch_init` it is checked to be `node_index = 0`.
When `is_branch_child` changes, it is checked to be `node_index = 15` in the previous row.

When `node_index != 15`, it is checked `is_last_branch_child = 0`.
When `node_index = 15`, it is checked `is_last_branch_child = 1`.

All these constraints are given in `branch.rs`.
Constraints to ensure the proper order of rows (after what row `is_branch_init` can appear,
for example) are given in `selectors.rs`.

<p align="center">
  <img src="./img/branch.png?raw=true" width="75%">
</p>

The picture presents a branch which has 14 empty nodes and 2 non-empty nodes.
The last two rows are all zeros because this is a regular branch,
not an extension node.

Each branch node row starts with 34 S proof columns and 34 C proof columns.
For non-empty rows, `rlp1` is always 160, because this denotes the length of the
substream which is 32 (= 160 - 128). The substream (in `advices`) in this case is hash of a
node.

When there is an empty node, the column looks like:

```
0, 0, 128, 0, ..., 0
```

Empty node in a RLP stream is denoted only by one byte - value 128.
MPT circuit uses padding with 0s to simplify the comparison
between S and C branch. This way, the branch nodes are aligned horizontally
for both proofs.

Non-empty nodes are at positions 3 and 11. Position 11 corresponds to the key (that
means the key nibble that determines the position of a node in this branch is 11) and
is stored in `modified_node` column.

`s_advices/c_advices` present the hash of a branch child.

One can observe that in position 3: `s_advices = c_advices`,
while in position 11: `s_advices != c_advices`.

That is because this is due to the modification at `key1` from `val1` to `val2`,
the nibble 11 corresponds to `key1`.

We need `s_advices/c_advices` for two things:

- to compute the overall branch RLC (to be able to check the hash of a branch to be in a parent)
- to check whether `s_advices/c_advices` (at `is_modified` position)
  present the hash of the next element in a proof

Branch in parent:

<p align="center">
  <img src="./img/branch_in_parent.png?raw=true" width="50%">
</p>

Extension node in parent:

<p align="center">
  <img src="./img/extension_in_parent.png?raw=true" width="50%">
</p>

The constraint for an element to be in a parent is implemented using lookups, for example:

```
lookup(branch RLC, branch length, hash RLC at is_modified in parent)
```

TODO: instead of 32 columns for `*_advices`, we could use only the RLC of `*_advices`.
To integrate `*_advices` RLC into the computation of the whole branch RLC, we
would just need to compute `mult * *_advices_RLC` and add this to the current RLC value.

To simplify the lookups, the hash of the modified node in branch S is stored in
`s_mod_node_hash_rlc` column. Similarly, for branch C in `c_mod_node_hash_rlc`.
It is checked that this value is the same in all 16 branch children rows.

<p align="center">
  <img src="./img/mod_node_hash_rlc.png?raw=true" width="50%">
</p>

Having the same value in all rows makes it easier to check that the value correspond
to the hash at `modified_node` position (otherwise it would be difficult to determine
the rotation in the row where the hash rlc would be stored because the `modified_node`
is not fixed).

The lookup for a branch is in `branch_hash_in_parent`. The lookup for an extension
node is in `extension_node.rs`.

### Computing branch RLC

The intermediate branch RLC is computed in each row, the final one is given in
`is_last_branch_child` row.

The constraints for RLC in branch init row are in `branch_rlc_init.rs`.

Note that the branch init contains the RLC bytes only in (some) of the first 10 columns.
The columns after this stores branch / extension node selectors.

The RLP of a branch can appear in two slightly different versions:

- At the beginning there appear two RLP meta bytes
- At the beginning there appear three RLP meta bytes

A branch with two RLP meta bytes looks like:

```
248, 81,... 
```

In this case, there are 81 bytes from position two onward in the branch RLP stream.
The RLC in this case should be `248 + 81r`.

A branch with three RLP meta bytes looks like:
`249, 1, 81,... `
This means there are 1 * 256 + 81 bytes from position three onward.
The RLC in this case should be `249 + 1r + 81r^2`.

The first two columns in init branch specify whether S branch has two or three RLP meta bytes:

- `1, 0` means two RLP meta bytes
- `0, 1` means three RLP meta bytes

Branch init RLP bytes:

- cols 2 and 3: whether branch C has 2 or 3 RLP meta data bytes
- cols 4 and 5: the actual branch S RLP meta data bytes
- col 6: the actual branch S RLP meta data byte (if there are 3 RLP meta data bytes in branch S)
- cols 7 and 8: branch C RLP meta data bytes
- col 9: the actual branch C RLP meta data byte (if there are 3 RLP meta data bytes in branch C)

The intermediate RLC values are stored in `acc_s` and `acc_c` columns for S and C branch
respectively.

<p align="center">
  <img src="./img/branch_rlc_init.png?raw=true" width="60%">
</p>

Two additional columns are needed: `acc_mult_s` and `acc_mult_c`.
These two columns are used to know with what multiplier should the next row begin with:

```
acc_s = acc_s_prev + s_rlp2 * acc_mult_s + s_advices[0] * acc_mult_s * r + s_advices[1] * acc_mult_s * r^2
```

<p align="center">
  <img src="./img/branch_rlc.png?raw=true" width="60%">
</p>

Constraints for `acc_s, acc_c, acc_mult_s, acc_mult_c`
being computed properly are in `branch_rlc.rs`.

There are two types of branch child: empty and non-empty. An empty child only contains
128 in `advices[0]` column, a non-empty child contains 160 in `rlp1` and then the child's
hash is given in 32 `advices` columns.
The constraints for `acc_s, acc_c, acc_mult_s, acc_mult_c` are thus simple because
there is in both cases a fixed number of columns used. For example, the constraint
for `acc_mult_s` for non-empty child would be:

```
acc_mult_s = acc_mult_s_prev * r^33
```

It is different in leaf rows where the number of columns used is not fixed as we will
see below.

In `is_last_branch_child` row, `acc_s` and `acc_c` contain the RLC of branch S and branch C
respectively.

### Branch length correspond to the RLP meta bytes

To check whether the length of the stream correspond to the length specified
with the RLP meta bytes, we use column 0. In each row we subtract the number
of bytes in a row. In the last row we checked whether the value is 1 (1 because
RLP length includes also ValueNode which occupies 1 byte).

<p align="center">
  <img src="./img/branch_length.png?raw=true" width="60%">
</p>

Note that branch node row can have either have 33 bytes or 1 byte. So, in each row,
the value in column 0 decreases by 33 or 1. These constraints are implemented in `branch.rs`.

### Address and key RLC in branch nodes

`modified_node` in the branch corresponds to one of the nibbles of key/address.
To check whether the proper key/address is used, key/address RLC is computed and
finally checked in the leaf row.
In each branch, an intermediate key/address RLC is checked to be computed properly.

<p align="center">
  <img src="./img/address_key_branch_rlc.png?raw=true" width="60%">
</p>

Two consecutive branches represent one byte of key/address. We need to know whether
the branch `modified_node` is the first or the second nibble of the key/address byte.
This information is given in branch init in two `s_advices` columns
`s_advices[IS_BRANCH_C16_POS - LAYOUT_OFFSET]` and
`s_advices[IS_BRANCH_C1_POS - LAYOUT_OFFSET]`.

If it is the first nibble, `modified_node` is multiplied by 16, otherwise by 1.
Constraints for
`s_advices[IS_BRANCH_C16_POS - LAYOUT_OFFSET]` and
`s_advices[IS_BRANCH_C1_POS - LAYOUT_OFFSET]`
are implemented in `branch_key.rs`.
For example, the two values need to be boolean, need to alternate (this alternating
gets more complicated when there is an extension node instead of a branch as it will be
discussed below), and the sum of the two needs to be 1.

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

#### Constraints

##### Constraint: selectors

There are six possible scenarios:

- extension node key contains only one nibble and `modified_node` needs to be
  multiplied by `16` for `key RLC`
- extension node key contains only one nibble and `modified_node` needs to be
  multiplied by `1` for `key RLC`
- extension node key contains even number of nibbles and `modified_node` needs to be
  multiplied by `16` for `key RLC`
- extension node key contains even number of nibbles and `modified_node` needs to be
  multiplied by `1` for `key RLC`
- extension node key contains odd number of nibbles (and more than 1) and `modified_node` needs to be multiplied by `16` for `key RLC`
- extension node key contains odd number of nibbles (and more than 1) and `modified_node` needs to be multiplied by `1` for `key RLC`

Extension node RLP encoding needs to be differently handled in different scenarios.
For example, in the the case of only one nibble, there is only one RLP meta byte
(key starts already in `s_rlp2`).

Key RLC information is packed together with information about number of nibbles to
reduce the expression degree.

It needs to be ensured that the selectors are boolean and their sum is `0` or `1`.
If it is `0`, there is a regular branch. If it is `1`, there is an extension node.
See `extension_node.rs` for the constraints.

Further, there are constraints that ensure the selector
value is correct. For example, when there is only one nibble, `s_rlp1` has to be `226`.
Also, when there is an even number of nibbles, `s_advices[0]` has to be `0`.

Information about key RLC multiplication factor is doubled to reduce the expression degree.
Thus the information appear in branch init row at the following positions:

```
pub const IS_BRANCH_C16_POS: usize = 19;
pub const IS_BRANCH_C1_POS: usize = 20;
pub const IS_EXT_SHORT_C16_POS: usize = 21;
pub const IS_EXT_SHORT_C1_POS: usize = 22;
pub const IS_EXT_LONG_EVEN_C16_POS: usize = 23;
pub const IS_EXT_LONG_EVEN_C1_POS: usize = 24;
pub const IS_EXT_LONG_ODD_C16_POS: usize = 25;
pub const IS_EXT_LONG_ODD_C1_POS: usize = 26;
```

There are constraints (`extension_node.rs`) that ensure the information at positions
`IS_BRANCH_C16_POS` and `IS_BRANCH_C1_POS` correspond to the information at positions
where extension node selectors are given.

##### Constraint: extension node RLC is properly computed

Extension node RLC needs to be prperly computed for both, S and C.
This is done by taking into account each byte of the extension node.
The RLC is computed in two steps: the first
step computes bytes in `s_rlp1', 's_rlp2`, `s_advices` (stored in `acc_s` column),
the second step in `c_rlp1', 'c_rlp2`, `c_advices` (stored in `acc_c` column).

First step:

```
rlc_s = s_rlp1 + s_rlp2 * r + s_advices[0] * r^2 + s_advices[1] * r^3 + ... + s_advices[31] * r^33 
```

Constraint:

```
rlc_s = acc_s
```

Second step:

```
rlc = rlc_first + c_rlp1 * r_1 + c_rlp2 * r_1^2 + c_advices[0] * r_1^3 + c_advices[1] * r_1^4 + ... + c_advices[31] * r_1^34 
```

Constraint:

```
rlc = acc_c
```

Note that not all `s_advices` are always used. In the above example, there is only
`0, 149`. The rest of `s_advices` are 0s. To ensure `s_advices` are 0 for `i > 1`,
`key_len_lookup` function is used (see below for a more detailed description).

For S:
`lookup(S branch RLC (retrived from the last branch children row), S branch RLC length, c_advices RLC in extension row)`.

For C extension node, the RLC from the first step from S extension node row is reused.
The second step is analogous to the S row, but uses the values from C row.

##### Constraint: hash of the extension node is in the parent branch

It needs to be checked that the extension node RLC is `mod_node_hash_rlc`
in the parent branch.

```
lookup(acc_c, extension node S length, s_mod_node_hash_rlc::(rot))
lookup(acc_c, extension node C length, c_mod_node_hash_rlc::(rot-1))
```

##### Constraint: hash of the underlying branch is in the extension node c_advices

For S:
`lookup(S branch RLC (retrived from the last branch children row), S branch length, c_advices RLC in extension row)`.

### Account leaf

There are five rows for an account leaf:

```
Key S
Nonce balance S
Nonce balance C
Storage codehash S
Storage codehash C
```

There is only one key row, because the key is always the same for the two parallel proofs.

<p align="center">
  <img src="./img/address_rlc.png?raw=true" width="60%">
</p>

### Storage leaf

There are five rows for a storage leaf:

```
Leaf key S
Leaf value S
Leaf key C
Leaf value C
Leaf in added branch
```

Note that leaf key S and leaf key C are not always the same - for example
when a value is added to the key which was empty, the leaf key C will be
shorter.

<!-- TestExtensionAddedOneKeyByteSel1-->

<!--
For example:
```
226,160,62,102,91,...
30,0,0...
225,159,58,134,125,...
17,0,0
225,159,54,91,73,...
```
-->

<p align="center">
  <img src="./img/storage_leaf.png?raw=true" width="60%">
</p>

##### Constraint: key RLC

<p align="center">
  <img src="./img/key_rlc.png?raw=true" width="60%">
</p>

The first row contains the storage leaf S key bytes. These bytes are what remains from the
key after key nibbles are used to navigate through branches / extension nodes.
That means key RLC that is being partially computed in branches / extension nodes can
be finalized here.

Intermediate key RLC `key_rlc_acc_start` is retrieved from the first branch children row.
Likewise, intermediate multiplication factor `key_mult_start` is retrieved from the same row.

```
```

... `key_len_lookup`

##### Constraint: leaf RLC

## Zeros in s_advices after substream ends

In various cases, `s_advices` are used only to certain point. Consider the example below:

```
228, 130, 0, 149, 0, ..., 0
```

In this example:

```
s_rlp1 = 228
s_rlp2 = 130
s_advices[0] = 0
s_advices[1] = 149
s_advices[2] = 0
...
s_advices[31] = 0
```

To prevent attacks on RLC, it needs to be checked that `s_advices[i] = 0` for `i > 1`:

```
s_advices[2] = 0
...
s_advices[31] = 0
```

The length of the substream is given by `s_rlp2`, it is `2 = 130 - 128` in the above example,
let us denote it by `len = 2`.

`s_advices[i]` are checked to be bytes.

Note that `(len - 1 - i) * s_advices[0] < 33 * 255` ensures `s_advices[i] = 0` for `i > len - 1`.

```
(len - 1) * s_advices[0] < 33 * 255
(len - 2) * s_advices[1] < 33 * 255
From now on, key_len < 0:
(len - 3) * s_advices[2] < 33 * 255 (Note that this will be true only if s_advices[2] = 0)
(len - 4) * s_advices[3] < 33 * 255 (Note that this will be true only if s_advices[3] = 0)
(len - 5) * s_advices[4] < 33 * 255 (Note that this will be true only if s_advices[4] = 0)
```

That is because when `len - i` goes below 0, it becomes a huge number close to field modulus.
Furthermore, `len` is at most 33.
If `len - i` is multiplied by `s_advices[i]` which is at most `255`, it will still be
bigger then `-32 * 255` which is much bigger than `33 * 255`.

See `key_len_lookup` in `helpers.rs` for the implementation.

## RLC multiplication factor after s_advices

As we have seen above,
in various cases, `s_advices` are used only to certain point. Consider the example below:

```
228, 130, 0, 149, 0, ..., 0
```

RLC is computed in two steps in such cases.
The first step computes bytes in `s_rlp1', 's_rlp2`, `s_advices` (stored in `acc_s` column),
the second step computes bytes in `c_rlp1', 'c_rlp2`, `c_advices` (stored in `acc_c` column).

First step:

```
rlc_first_step = s_rlp1 + s_rlp2 * r + s_advices[0] * r^2 + s_advices[1] * r^3 + ... + s_advices[31] * r^33 
```

Constraint

```
rlc_first_step = acc_s
```

Note that the RLC is computed and assigned in the `sythesize` function, the chips then
verify whether that the computation is correct.

In the next step:

```
rlc = rlc_first + c_rlp1 * r_1 + c_rlp2 * r_1^2 + c_advices[0] * r_1^3 + c_advices[1] * r_1^4 + ... + c_advices[31] * r_1^34 
```

Constraint:

```
rlc = acc_c
```

It also needs to be checked that `r_1` corresponds to `len`:

```
r_1 = r^(len+2)
```

This is checked using a lookup into a table:

```
(RMult, 0, 1)
(RMult, 1, r)
(RMult, 2, r^2)
(RMult, 3, r^3)
...
(RMult, 65, r^65)
```

The lookup looks like:

```
lookup(RMult, len+2, r_1)
```

See `mult_diff_lookup` in `helpers.rs` for the implementation.
