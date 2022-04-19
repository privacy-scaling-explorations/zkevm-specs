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
row is a branch node or a leaf node.

34 columns presents 2 + 32.
The first 2 columns are RLP specific as we will see below.
32 columns are used because this is the length of hash output.
Note that, for example, each branch node is given in a hash format -
it occupies 32 positions.

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

Extension node (the two extension node rows are non-empty):

<p align="center">
  <img src="./img/extension_node.png?raw=true" width="50%">
</p>

Boolean selectors `is_branch_init`, `is_branch_child`, `is_last_branch_child`,
`is_modified` are used to trigger the constraints only when necessary.
Two examples:

- Checking that hash of a branch RLP is in the parent element
  (branch / extension node) is done in the last branch row (`is_last_branch_child`)
- S and C children are checked to be the same in all rows except at `is_modified`.

There are two other columns that ensure that branch rows follow
the prescribed layout: `node_index` and `modified_node`.

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
After `is_branch_init` it is checked to be a row with  `is_branch_child = 1`.
After `is_branch_init` it is checked to be a row `node_index = 0`.
When `is_branch_child` changes, it is checked to be `node_index = 15` in the previous row.

When `node_index != 15`, it is checked that `is_last_branch_child = 0`.
When `node_index = 15`, it is checked that `is_last_branch_child = 1`.

All these constraints are implemented in `branch.rs`.
Constraints to ensure the proper order of rows (after what row `is_branch_init` can appear,
for example) are implemented in `selectors.rs`.

<p align="center">
  <img src="./img/branch.png?raw=true" width="75%">
</p>

The picture presents a branch which has 14 empty nodes and 2 non-empty nodes.
The last two rows are all zeros because this is a regular branch,
not an extension node.

Each branch node row starts with 34 S proof columns and 34 C proof columns.
For non-empty rows, `rlp1` is always 160:

```
0, 160, 55, 235, ...
```

This is because 160 denotes (in RLP encoding) the length of the
substream which is 32 (= 160 - 128). The substream in this case is hash
of a branch child.

When there is an empty node, the column looks like:

```
0, 0, 128, 0, ..., 0
```

Empty node in a RLP stream is denoted only by one byte - by value 128.
However, MPT circuit uses padding with 0s - empty node occupies the whole row too.
This is too simplify the comparisons
between S and C branch. This way, the branch nodes are aligned horizontally
for both proofs.

Non-empty nodes in the above picture are at positions 3 and 11.
Position 11 corresponds to the key (that
means the key nibble that determines the position of a node in this branch is 11) and
is stored in `modified_node` column.

`s_advices/c_advices` present the hash of a branch child.

One can observe that in position 3: `s_advices = c_advices`,
while in position 11: `s_advices != c_advices`.

That is because the nibble 11 corresponds to `key1` where the storage modification
occured. The branch at position 3 is not affected by this storage modification.

We need `s_advices/c_advices` for two things:

- To compute the overall branch RLC (to be able to check the hash of a branch RLP to be in a parent) - in this case, `s_advices/c_advices` is a substream of RLP stream, we need to compare hash of the whole RLP stream to be in a parent
- To check whether `s_advices/c_advices` (at `is_modified` position)
  present the hash of the next element in a proof - in this case, `s_advices/c_advices`
  presents hash that is to be compared to be the hash of the underlying element.

Checking branch hash in a parent:

<p align="center">
  <img src="./img/branch_in_parent.png?raw=true" width="50%">
</p>

Checking extension node hash in a parent:

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
`s_mod_node_hash_rlc` column. Similarly, for branch C it is stored in `c_mod_node_hash_rlc`.
It is checked that this value is the same in all 16 branch children rows.

<p align="center">
  <img src="./img/mod_node_hash_rlc.png?raw=true" width="50%">
</p>

Having the same value in all rows makes it easier to check that the value corresponds
to the hash at `modified_node` position: otherwise it would be difficult to determine
the rotation to the row where hash rlc is stored because `modified_node`
is not fixed.

The lookup constraints for branch are implemented in `branch_hash_in_parent`. The lookup constraints for extension node are implemented in `extension_node.rs`.

### Computing branch RLC

The intermediate branch RLC is computed in each row, the final one is given in
`is_last_branch_child` row.

Branch init row contains the RLC bytes only in (some) of the first 10 columns.
The columns after this stores branch / extension node selectors.

The RLP of a branch can appear in two slightly different versions:

- At the beginning there are two RLP meta bytes
- At the beginning there are three RLP meta bytes.

A branch with two RLP meta bytes looks like:

```
248, 81,... 
```

In this case, there are 81 bytes from position two onward in the branch RLP stream.
The intermediate RLC in this case should be `248 + 81r`.

A branch with three RLP meta bytes looks like:

```
249, 1, 81,...
```

This means there are 1 * 256 + 81 bytes from position three onward.
The intermediate RLC in this case should be `249 + 1r + 81r^2`.

Columns 0 and 1 in branch init row specify whether S branch has two or three RLP meta bytes:

- `1, 0` means two RLP meta bytes
- `0, 1` means three RLP meta bytes.

Similarly, columns 2 and 3 specify
whether C branch has two or three RLP meta bytes.

Further branch init RLP bytes:

- Columns 4 and 5: the actual branch S RLP meta data bytes
- Column 6: the actual branch S RLP meta data byte (if there are 3 RLP meta data bytes in branch S)
- Columns 7 and 8: branch C RLP meta data bytes
- Column 9: the actual branch C RLP meta data byte (if there are 3 RLP meta data bytes in branch C)

The intermediate RLC values are stored in `acc_s` and `acc_c` columns for S and C branch
respectively.

The constraints for RLC in branch init row are implemented in `branch_rlc_init.rs`.

<p align="center">
  <img src="./img/branch_rlc_init.png?raw=true" width="60%">
</p>

To check the intermediate RLC for `is_branch_child` rows,
two additional columns are needed: `acc_mult_s` and `acc_mult_c`.
These two columns are used to know with what multiplier should be used in the next row:

```
acc_s = acc_s_prev + s_rlp2 * acc_mult_s_prev + s_advices[0] * acc_mult_s_prev * r + s_advices[1] * acc_mult_s_prev * r^2
```

<p align="center">
  <img src="./img/branch_rlc.png?raw=true" width="60%">
</p>

Constraints for `acc_s, acc_c, acc_mult_s, acc_mult_c`
are implemented in `branch_rlc.rs`.

There are two types of branch child: empty and non-empty.
Both has a fixed number of bytes (33 and 1) which simplifies
the constraints for `acc_s, acc_c, acc_mult_s, acc_mult_c`.
For example, the constraint
for `acc_mult_s` for non-empty child would be:

```
acc_mult_s = acc_mult_s_prev * r^33
```

On the other hand, leaf rows do not have a fixed number of bytes (key in a leaf
can be of different lengths) which require more complex constraints as is described
below.

In `is_last_branch_child` row, columns `acc_s` and `acc_c` contain the RLC of branch S and branch C respectively. These two values are compared to be the same as
the intermediate RLC values in the last branch children row.

### Branch length corresponds to the RLP meta bytes

As discussed above, branch RLP can have two or three RLP meta bytes that specify
its length.
To check whether the actual length of the stream corresponds to the length specified
with the RLP meta bytes, column 0 is used (`s_rlp1, c_rlp1`).
In each row we subtract the number
of bytes in a row: 33 for non-empty row, 1 for empty row.
In the last row we checked whether the value is 1.

The final value should be 1 (and not 0) because
RLP length includes also ValueNode which occupies 1 byte and is not stored in MPT layout.

<p align="center">
  <img src="./img/branch_length.png?raw=true" width="30%">
</p>

Constraints for RLP length are implemented in `branch.rs`.

### Address and key RLC in branch nodes

To check that storage modification occurs at the proper address / key,
the circuit computes intermediate address RLC / key RLC at each branch / extension node. The final address RLC is computed in `is_account_leaf` row, the final
key RLC is computed in `is_leaf_key` row.

In each branch,
`modified_node` corresponds to one of the nibbles of the key/address.

<p align="center">
  <img src="./img/address_key_branch_rlc.png?raw=true" width="60%">
</p>

Let us say the address (after being hashed) is composed of the following nibbles:

```
n0 n1 n2 ... n63
```

This means the bytes are:

```
(n0 * 16 + n1) (n2 * 16 + n3) ... (n62 * 16 + n63)
```

`modified_node` in one branch / extension node corresponds to one nibble, two
consecutive elements (each branch or extension node) corresponds to one byte.

To compute the RLC, we need to know whether
the branch / extension node is the first or second nibble of a byte.
This information is given in branch init row in two `s_advices` columns:
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

When does extension node appear?

Let us observe the leaf in the picture below.

<p align="center">
  <img src="./img/leaf.png?raw=true" width="40%">
</p>

The leaf appears at position `n3` in the branch. Its parent branch appears at position `n2` in
its own parent. Likewise for `n1` and `n0` (`n0` is position in the root branch).

The rest of the nibbles are stored in the leaf.

There are three possible storage modification scenarios:

- If the storage modification occurs at the same key (all 64 nibbles match), the
  value in the leaf will be updated.
- If the storage modification occurs at the key where `n0 n1 n2 n3` match,
  a branch is inserted instead of a leaf. Let us say the nibbles of the key where
  change occurs are: `n0 n1 n2 n3 m4 m5 ... m63`. The new branch contains two leaves:
  the old one at position `n4` and the new one at position `m4`.
- If the storage modification occurs at the key where `n0 n1 n2 n3` match and
  also some further nibbles match, for example: `n4 = m4, n5 = m5, n6 = m6`,
  an extension node is inserted instead of a leaf. Extension node is like a leaf,
  it contains key (which stores nibbles, in our example: `n4 n5 n6`) and value which is
  a hash of the new branch. As in the second scenario, the new branch contains two leaves:
  the old one at position `n7` and the new one at position `m7` (where `n7 != m7`).

Leaf into branch:

<p align="center">
  <img src="./img/into_branch.png?raw=true" width="35%">
</p>

Leaf into extension node:

<p align="center">
  <img src="./img/into_extension.png?raw=true" width="35%">
</p>

Extension node can be viewed as a special branch. It contains a regular branch,
but to arrive to this branch there is an extension - additional nibbles to be
navigated. In the picture, the extension is: `n4 n5 n6`.

The extension node element returned by `eth getProof` thus appear
as leaf. It contains:

- In the key: the information about nibbles in the leaf key.
- In the value: the hash of the underlying branch.

For example, the `eth getProof` returns:

```
228,130,0,149,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249
```

The key (information about nibbles) is stored in:

```
0 149
```

The value (branch hash) is stored in:

```
114 253 150 ...
```

The second byte (130) means there are two (130 - 128) bytes compressing the nibbles.
These two bytes are `0, 149` and they represent
the two nibbles: 9 and 5 (149 = 9 * 16 + 5).

The bytes after 160 represent a hash of the underlying branch.

The layout uses `s_rlp1`, `s_rlp2`, and `s_advices` for RLP meta bytes and nibbles,
while `c_advices` are used for branch hash, and `c_rlp2` stores 160 (denoting the number of hash bytes).

<p align="center">
  <img src="./img/extension_node_row.png?raw=true" width="45%">
</p>

There are two extension node rows - one for S proof, one for C proof.
However, the extension key (nibbles) is the same for S and C, we do not need
to duplicate this information.
For this reason, in C row, we do not put key into `s_rlp1`, `s_rlp2`, and `s_advices`,
we just put hash of C underlying branch in `c_advices`.

But we do not leave `s_rlp1, s_rlp2, s_advices` empty in C row, we store additional witness for
nibbles there because nibbles are
compressed into bytes and it is difficult to decompress back into nibbles
without any helper witnesses. This is not needed in all cases though, as we will see below.

Thus, the two extension rows look like:

<!--
generated with TestExtensionTwoKeyBytesSel1
-->

```
[228,130,0,149,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249]
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,57,70,87,80,220,197,201,254,196,232,29,240,104,158,250,223,175,172,44,123,126,255,126,108,15,160,185,239,174,205,146,130]
```

The first row contains:

- `s_advices`: extension (nibbles `3`, `9`, and `5` compressed into bytes)
- `c_advices`: hash of S branch

The second row contains:

- `s_advices`: the second nibble of each byte stored in the first row
- `c_advices`: hash of C branch

In extension node, the intermediate `key_rlc` is computed by taking `key_rlc` and `key_rlc_mult`
(denoted by `key_rlc_prev` and `key_rlc_mult`)
from the parent element and adding the extension node bytes.
However, the calculation depends on:

- How many nibbles have already been used in the branches / extension nodes above
- Whether there are even or odd nibbles in the extension.

These different cases are the reason for a rather heavy branching in the `extension_node_key`.

#### Even nibbles above, even nibbles in extension

Even nibbles in extension means no nibble will be stored at `s_advices[0]`.

```
key_rlc = key_rlc_prev + s_advices[1] * key_rlc_mult + s_advices[2] * key_rlc_mult * r + ...
```

For the example above this would mean:

```
key_rlc = key_rlc_prev + 149 * key_rlc_mult
```

#### Even nibbles above, odd nibbles in extension

Odd nibbles in extension means one nibble will be stored at `s_advices[0]`.

This is the case when the second nibbles witnesses are needed. For example:

```
[228,130,16+3,9*16+5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249]
[0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,57,70,87,80,220,197,201,254,196,232,29,240,104,158,250,223,175,172,44,123,126,255,126,108,15,160,185,239,174,205,146,130]
```

In the second row, 5 presents the second nibble of 149 (149 = 9 * 16 + 5).
Having the second nibble simplifies the computation of the first nibble (including both, first
and second nibbles, as witnesses is not possible as there is not enough space in `s_advices` for
cases where extension would be more than 32 nibbles).

In this case, the intermediate `key_rlc` is computed:

```
key_rlc = key_rlc_prev + ((s_advices[0] - 16) * 16 + s_advices[1]_first_nibble) * key_rlc_mult + (s_advices[1]_second_nibble * 16 + s_advices[2]_first_nibble) * key_rlc_mult * r + ...
```

For the example above:

```
key_rlc = key_rlc_prev + (3 * 16 + 9) * key_rlc_mult + 5 * 16 * key_rlc_mult + r
```

#### Odd nibbles above, even nibbles in extension

Even nibbles in extension means no nibble will be stored at `s_advices[0]`.
The second nibbles witnesses are needed here:

```
key_rlc = key_rlc_prev + s_advices[1]_first_nibble * key_rlc_mult + (s_advices[1]_second_nibble * 16 + s_advices[2]_first_nibble) * key_rlc_mult * r + ...
```

For example:

```
[228,130,0,9*16+5,8*16+4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249]
[0,0,5,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,57,70,87,80,220,197,201,254,196,232,29,240,104,158,250,223,175,172,44,123,126,255,126,108,15,160,185,239,174,205,146,130]
```

```
key_rlc = key_rlc_prev + 9 * key_rlc_mult + (5 * 16 + 8) * key_rlc_mult * r + 4 * 16 * key_rlc_mult * r^2
```

#### Odd nibbles above, odd nibbles in extension

Odd nibbles in extension means one nibble will be stored at `s_advices[0]`. We do not need the second
nibbles witnesses here:

```
key_rlc = key_rlc_prev + (s_advices[0] - 16) * key_rlc_mult + s_advices[1] * key_rlc_mult * r + s_advices[2] * key_rlc_mult * r^2 + ...
```

For example:

```
[228,130,16+3,149,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249]
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,57,70,87,80,220,197,201,254,196,232,29,240,104,158,250,223,175,172,44,123,126,255,126,108,15,160,185,239,174,205,146,130]
```

```
key_rlc = key_rlc_prev + 3 * key_rlc_mult + 149 * key_rlc_mult * r
```

#### Only one nibble

When there is only one nibble, there is no byte specifying the length of the key extension
(130 in the above cases).
For example, in the case below, the nibble is 0 (16 - 16):

`226,16,160,172,105,12...`

In this case, the second nibble witnesses are not needed too.

There are two subcases. When there are even nibbles above:

```
key_rlc = key_rlc_mult + (s_rlp2 - 16) * 16 * key_rlc_mult
```

And when there are odd nibbles above:

```
key_rlc = key_rlc_mult + (s_rlp2 - 16) * key_rlc_mult
```

### Selectors

The following selectors are used to handle the computation of `key_rlc`. The following witnesses
are stored in branch init row:

- `is_branch_c16`: whether the branch `modified_node` needs to be multiplied by 16 when computing `key_rlc`
- `is_branch_c1`: whether the branch `modified_node` needs to be multiplied by 1 when computing `key_rlc`
- `is_ext_short_c16`: whether the extension is of length 1 and the branch `modified_node` needs to be multiplied by 16 when computing `key_rlc`
- `is_ext_short_c1`: whether the extension is of length 1 and the branch `modified_node` needs to be multiplied by 1 when computing `key_rlc`
- `is_ext_long_even_c16`: whether the extension is of even length and the branch `modified_node` needs to be multiplied by 16 when computing `key_rlc`
- `is_ext_long_even_c1`: whether the extension is of even length and the branch `modified_node` needs to be multiplied by 1 when computing `key_rlc`
- `is_ext_long_odd_c16`: whether the extension is of odd length (and more than 1) and the branch `modified_node` needs to be multiplied by 16 when computing `key_rlc`
- `is_ext_long_odd_c1`: whether the extension is of odd length (and more than 1) and the branch `modified_node` needs to be multiplied by 1 when computing `key_rlc`

Multiple bits of information are used to reduce the expression degree.

It needs to be ensured that the selectors are boolean. Further, the sum of `ext` selectors
needs to be `0` or `1`.
If it is `0`, there is a regular branch. If it is `1`, there is an extension node.
See `extension_node.rs` for the constraints.

Further, there are constraints that ensure the selector
value is correct. For example, when there is only one nibble, `s_rlp1` has to be `226`.
Also, when there is an even number of nibbles, `s_advices[0]` has to be `0`.

There are constraints (`extension_node.rs`) that ensure the information at positions
`IS_BRANCH_C16_POS` and `IS_BRANCH_C1_POS` correspond to the information at positions
where extension node selectors are given.

## Account leaf

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

## Storage leaf

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

Storage leaf can appear in two RLP formats:

- Short: if leaf RLP length is less or equal 55, it has only two RLP meta bytes, like:

```
[226,160,59,138,106,70,105,186,37,13,38,205,122,69,158,202,157,33,95,131,7,227,58,235,229,3,121,188,90,54,23,236,52,68,1]
```

In the above example `226 160` are RLP meta data bytes. 226 means the length of leaf RLP (behind this byte) is 34 (226 - 192). 160 means there are 32 (160 - 128) bytes in the
following substream that represents the `key` (compressed nibbles).
Finally, there is a last byte that represents the leaf value: 1.

Leaf RLP: `226 (representing leaf length: 34) 160 (representing key length: 32) 59 ... 68 (32 bytes representing key) 1 (representing value)`.

- Long: if leaf RLP length is more than 55, it has only two RLP meta bytes, like:

```
[248,67,160,59,138,106,70,105,186,37,13,38,205,122,69,158,202,157,33,95,131,7,227,58,235,229,3,121,188,90,54,23,236,52,68,161,160,187,239,170,18,88,1,56,188,38,60,149,117,120,38,223,78,36,235,129,201,170,170,170,170,170,170,170,170,170,170,170,170]
```

In this example, `248 67 160` are RLP meta bytes. 248 means there is 1 byte (248 - 247)
specifying the length of RLP. This byte is 67 - there are 67 bytes after this byte.
160 means there are 32 bytes in the substream that follows and represents the `key`.
`161 160` represents RLP meta bytes for leaf `value`. 161 represents length 31 (161 - 128),
160 represents length 32 (160 - 128) which is the length of the actual value: `187 239 ... 170`.

Leaf RLP: `248 67 (representing leaf length) 160 (representing key length: 32) 59 ... 68 (32 bytes representing length) 161 160 (representing value length: 32) 187 ... 170 (representing value)`.

### Key RLC in storage leaf

<p align="center">
  <img src="./img/key_rlc.png?raw=true" width="60%">
</p>

The first row contains the storage leaf S key bytes. These bytes are what remains from the
key after key nibbles are used to navigate through branches / extension nodes.
That means: key RLC that is being partially computed in branches / extension nodes can
be finalized here.

Let us say there are two branches above the leaf as in the picture above.
The intermediate key RLC is thus: `n0 * 16 + n1`
where `n1` is the position of the leaf in the second branch and `n0` is the position
of the second branch in the first branch.

The remaining key nibbles (`n2 ... n63`) are stored in `leaf key` row.
The final `key_rlc` to be computed is:

```
(n0 * 16 + n1) + (n2 * 16 + n3) * r + ... + (n62 * 16 + n63) * r^31
```

This computation depends on two things:

- Whether it is short or long RLP (see above).
- Whether the remaining number of nibbles is even or odd.

Key nibbles are stored from position 2 (short RLP) or 3 (long RLP) onward.

Let observe how the even or odd number of the remaining key nibbles affects the computation
using two examples. The two selectors to determine whether it is the even or odd case is retrieved
from the branch init row (IS_BRANCH_C16_POS, IS_BRANCH_C1_POS). The constraints for
these selectors are implemented in `branch_key`.

#### Example with even number of remaining nibbles

Let us have the following key RLP:

```
[226, 160, 32, 16 * 3 + 2, 16 * 8 + 4, ...
```

32 means there are even number of remaining nibbles. The remaining nibbles are:
`3, 2, 8, 4, ...`.
To compute `key_rlc`, the intermediate `key_rlc_prev` and `key_rlc_mult_prev` are retrieved
from the branch above:

```
key_rlc = key_rlc_prev + (16 * 3 + 2) * key_rlc_mult_prev + (16 * 8 + 4) * key_rlc_mult_prev * r + ...
```

#### Example with odd number of remaining nibbles

Let us have the following key RLP:

```
[226, 160, 48 + 7, 16 * 3 + 2, 16 * 8 + 4, ...
```

48 + 7 means the first of the remaining nibbles is 7. `key_rlc` is computed:

```
key_rlc = key_rlc_prev + 7 * key_rlc_mult_prev + (16 * 3 + 2) * key_rlc_mult_prev * r + (16 * 8 + 4) * key_rlc_mult_prev * r^2 + ...
```

### Leaf RLC

Leaf RLC is computed in both, `leaf key` row and `leaf value` row.
It goes over all leaf RLP bytes (`b0 b1 ... bl`) and computes:

```
b0 + b1 * r + ... + bl * r^l
```

The intermediate RLC is computed in `leaf key` row, this value (`leaf_rlc_prev`) is then retrieved in `leaf value` row and used for the final computation.

Leaf hash is checked to be in the parent branch / extension node at the
`modified_node` position.

However, there are a couple of special case when check of the hash needs to be handled
separately.

#### Case 1: Leaf turns into branch / extension node

Let us observe the case where storing a value turns a leaf into a branch or extension node.
Let us say we have `Leaf 1` and we set
value `val` at key `key` which will result in `Leaf 2`.

In this case S proof will be shorter than C proof.
The layout would look like:

```
Branch 1 | Branch 1
         | Branch 11
Leaf 1   | Leaf 2
```

`Leaf 1` is replaced by `Branch 11`. `Branch 11` contains two leaves: `Leaf 1` and `Leaf 2`.
However, `Leaf 1` has a shorter key now. To enable the verification that `Branch 11` contains
only two leaves and one of them is `Leaf 1` (with shorted key), the modified `Leaf 1` is stored
in the fifth storage leaf row (`Leaf in added branch`). It is ensured that the values
in this row correspond to `Leaf 1`.

<p align="center">
  <img src="./img/placeholder_branch.png?raw=true" width="50%">
</p>

In order not to break the layout, a placeholder branch is added in S
proof. This way, the leaf S and leaf C are positioned one after another as in other cases
(where the number of branches above the leaf S and leaf C is the same).

To make it simpler, for the placeholder branch its paralell counterpart is used (when
S branch is a placeholder, C branch is used as a placeholder; when C branch is a placeholder,
S branch is used as a placeholder).

This way, the equalities between S and C branch still holds.
On the other hand, the constraint for branch hash to be in a parent element is switched off.
Instead, the hash of a leaf is checked to be in an element that is above the placeholder
branch.

In case when there are two leaves in a branch and one of them is deleted, the scenario is
reversed: C proof contains placeholder branch.

#### Case 2: Key not used yet

Let us say no value is set at key `key`.
After setting the value at `key`, S proof would not have a leaf, while C proof would have it:

```
Branch 1 | Branch 1
         | Leaf 2
```

To preserve the layout a placeholder leaf `Leaf 1` is added:

```
Branch 1 | Branch 1
Leaf 1   | Leaf 2
```

In this case, the leaf constraints are switched off for the placeholder leaf.
Instead, it is checked that there is an empty row in branch at `modified_node` position.

<p align="center">
  <img src="./img/storage_leaf_placeholder.png?raw=true" width="50%">
</p>

The information whether the leaf is a placeholder is stored in `sel1` and `sel2` columns
in branch rows (in all rows to simplify the constraints, similarly as `modified_node`, see
above).

Note that when the key is deleted, the scenario is reversed: C proof constains the placeholder
leaf.

#### Case 3: Key in first level - leaf turns into branch / extension node

<p align="center">
  <img src="./img/one_leaf_in_trie.png?raw=true" width="50%">
</p>

#### Case 4: Key in first level - key not used yet

## Lookups into MPT

Lookups for `nonce`, `balance`, and `codehash` modifications are enabled in account
leaf rows.
Account leaf rows are the following:

```
Key S
Nonce balance S
Nonce balance C
Storage codehash S
Storage codehash C
```

Lookup for `nonce` and `balance` modifications are enabled in the third
account leaf row (`Nonce balance C`).
To enable lookups, this row contains `nonce` and `balance` S (previous) and C (current) values
(their RLCs).

`nonce` lookup should check for the following fields:

```
counter, address_rlc, nonce_s_rlc, nonce_c_rlc, is_nonce_mod
```

`balance` is to be ignored in `nonce` lookup, but it is ensured that it does not change
when `is_nonce_mod` (meaning `balance_s_rlc = balance_c_rlc`).

Similarly,
`balance` lookup should check for the following fields:

```
counter, address_rlc, balance_s_rlc, balance_c_rlc, is_balance_mod
```

Lookup for `codehash` modifications is enabled in the fifth
account leaf row (`Storage codehash C`).
To enable lookups, this row contains `codehash` S (previous) and C (current) values
(their RLCs).

`codehash` lookup should check for the following fields:

```
counter, address_rlc, codehash_s_rlc, codehash_c_rlc, is_codehash_mod
```

Differently, storage modification lookup is enabled in the storage leaf value C row.
Storage leaf rows are the following:

```
Leaf key S
Leaf value S
Leaf key C
Leaf value C
Leaf in added branch
```

To enable lookups, `Leaf value C` row contains leaf value S (previous) and leaf value C
(current) RLCs, as well as leaf key C RLC.

`storage` lookup should check for the following fields:

```
counter, address_rlc, key_rlc, value_s_rlc, value_c_rlc, is_storage_mod
```

Selectors `is_nonce_mod`, `is_balance_mod`, `is_codehash_mod`, `is_storage_mod` are ensured
to be booleans and their sum is ensured to be 1. It is ensured that only one modification
takes place at once.

`address_rlc` used in `storage` lookup is ensured to be the same as computed in the
`account leaf key` row. This is done by checking that the value in `address_rlc` column
does not change when passing down from `account leaf key` row to `leaf value C` row.

Note that that the attacker could try to omit the account proof and providing just
a storage proof with the appropriate `address_rlc` value. This would enable `storage`
lookups where the attacker would avoid triggering all account proof related constraints.
However, this is prevented by ensuring each storage proof has a corresponding account
proof (by checking `address_rlc` starts with 0 value in the first level of the proof
and can be changed only in `account leaf key` row).

## Helper techniques

### Zeros in s_advices after substream ends

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

### RLC multiplication factor after s_advices

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
