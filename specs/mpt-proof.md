# Merkle Patricia Trie (MPT) Proof


## 0. Quick recap

- We validate the change of two storage proofs, from proof S(tate) to proof C(changed), where only one modification (`is_nonce_mod` or `is_balance_mod` or `is_codehash_mod` or `is_storage_mod` )  
- Each proof consists in: path-to-acount-leaf + accout-leaf + path-to-storage + storage-leaf
- path-to-xxxx are a list of circuit-branch. Each circuit-branch has a set of rows: init, 16 nodes and two "optional MPT extension" after it. So a branch and its optional following extension are considered together.
- Checking keccak hashes are done by doing lookup into a RLP => Keccak table
- Mainly we needs to prove the following constrains
  - Hash of a branch is in the parent (see _Checking branch hash in a parent_)
     - Compute branch-leaf RLC ( see _Compute branch RLC_ )
     - Check branch-leaf length is correct ( see _Branch length corresponds to the RLP meta bytes_ )
     - In the case that branch contains an extension, check also extension is in the parent ( see _Checking extension node hash in a parent_)
  - Merkle path to account-leaf is correct
      - Merkle path for the account address is keccak(address)
      - Compute address RLC incrementally in each node ( see _Address and Key in branch nodes_)  
      - Compute extension RLC ( see _Extension node rows_ , `key_rlc` 4 branching computation ) 
  - account-leaf hash is correct
     - Compute account-leaf RLC ( see _Account leaf_ )
  - Merkle path to storage-leaf is correct ( see _Key RLC in storage leaf_ )
  - storage-leaf hash is correct ( see _Leaf RLC_ ) with 4 options
- The following lookups can be done:
  - for nonce [`counter`,`address_rlc`,`nonce_s_rlc`, `nonce_c_rlc`, `is_nonce_mod`]
  - for balance [`counter`,`address_rlc`,`balance_s_rlc`,`balance_c_rlc`,`is_balance_mod`]
  - for codehash [`counter`,`address_rlc, `codehash_s_rlc`, `codehash_c_rlc`, `is_codehash_mod`]
  - for storage [`counter`,`address_rlc`, `key_rlc`, `value_s_rlc`,`value_c_rlc`, `is_storage_mod`]

## 1. Pre-requisites

- Read about [RLP encoding](https://ethereum.org/en/developers/docs/data-structures-and-encoding/rlp/)
  - See [RLP encoded/decoder online](https://codechain-io.github.io/rlp-debugger/)
- Read about [Patricia Merkle Tree](https://ethereum.org/en/developers/docs/data-structures-and-encoding/patricia-merkle-trie/#top)

## 2. Intro

MPT circuit checks that the modification of the trie state happened correctly.

Let's assume there are two proofs (as returned by `eth getProof`):

- A proof S(tate) that there exists value `val1` at key `key1` for address `addr` in the state trie with root `root1`.
- A proof C(hanged) that there exists value `val2` at key `key1` for address `addr` in the state trie with root `root2`.

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

See a real example of data in _Geth proofs examples_ section.

### 2.1 Basic checks

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

### 2.2 Expected RLP patterns in 

Not all possibilities exists in the MPT RLPs, we expect the following RLP patterns to appear in the geth proofs:

In account 

- In branches: 17-element RLP `[ <128|hash> (16 times) , 128]`
- In extensions: 2-element RLP `[ nibble 2|3 + path nibbles , hash ]` 
- In leafs:  2-element RLP `[ nibble 0|1 + path nibbles , rlp-list[ nonce, balance, storage-trie-root, codechash ] ]`

In storage

- In branches: **fix**
- In extensions:
- In leafs: 

note `128` means an empty value
note `hash` is 32 bytes

### 2.3 General circuit layout

The two parallel proofs are called S proof and C proof in the MPT circuit layout.

The first 34 columns are for the S proof.
- 2 columns are RLP specific as we will see below.
  - `s_rlp1`
  - `s_rlp2`
- 32 columns are used because this is the length of hash output. Note that, for example, each branch node is given in a hash format -
it occupies 32 positions.
  - `s_advices` (32 columns)

The next 34 columns are eactly the same but for the C proof.
- `c_rlp1`
- `c_rlp2`
- `c_advices` (32 columns)

The remaining columns are selectors, for example, for specifying whether the
row is a branch node or a leaf node.

## 3. Branch / extension node layout

### 3.1 Branch

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

#### 3.1.1 Ensure correctness of helper selectors 

Boolean selectors `is_branch_init`, `is_branch_child`, `is_last_branch_child`,
`is_modified` are used to trigger the constraints only when necessary.

Two examples:

- Checking that hash of a branch RLP is in the parent element
  (branch / extension node) is done in the last branch row (`is_last_branch_child`) 
- S and C children are checked to be the same in all rows except at `is_modified`.

There are two other columns that ensure that branch rows follow
the prescribed layout: `node_index` and `modified_node`.

- **§1** `node_index` is checked to be running monotonously from 0 to 15.
This way it is ensured that branch layout really has 16 branch children rows.

- `modified_node` specifies the index at which the storage modification in this branch occured.
**§2** `modified_node` is checked to be the same in all branch children rows - having this value
available in all rows simplifies the constraints for checking that `is_modified` is true
only when `node_index - modified_node = 0`. Having `modified_node` available only in one row,
it would be difficult to write a constraint for `node_index - modified_node = 0` for all
16 rows.

- **§3** `is_last_branch_child` is checked to be in the row with `node_index` = 15.
`is_branch_child` is checked to follow either `is_branch_init` or `is_branch_child`.
- **§4** After `is_branch_init` it is checked to be a row with  `is_branch_child = 1`.
- **§5** After `is_branch_init` it is checked to be a row `node_index = 0`.
- **§6** When `is_branch_child` changes, it is checked to be `node_index = 15` in the previous row.

- **§7** When `node_index != 15`, it is checked that `is_last_branch_child = 0`.
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

#### 3.1.2 Witness branch in the circuit

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

Multiple bits of information are packed into selectors to reduce the expression degree.
It is ensured that `is_branch_c16` and `is_branch_c1` correspond properly to `c16/c1`
part of extension node selectors.

It needs to be ensured that the selectors are boolean. Further, the sum of `ext` selectors
needs to be `0` or `1`.
If it is `0`, there is a regular branch. If it is `1`, there is an extension node.
See `extension_node.rs` for the constraints.

Further, there are constraints that ensure the selector
value is correct. For example, when there is only one nibble, `s_rlp1` has to be `226`.
Also, when there is an even number of nibbles, `s_advices[0]` has to be `0`.

## Account leaf

There are seven rows for an account leaf:

```
Key S
Key C
Nonce balance S
Nonce balance C
Storage codehash S
Storage codehash C
Leaf in added branch
```

<p align="center">
  <img src="./img/address_rlc.png?raw=true" width="60%">
</p>

Only one modification is allowed at a time, thus S proof and C proof differ in one
of the following:

- Nonce
- Balance
- Storage trie root
- Codehash

When `nonce`, `balance`, or `codehash` is modified, there is no storage proof and
no rows below account leaf. When `storage` is modified, it is ensured that there
is a storage proof (via `address_rlc` being changed only in one of storage
leaf rows; `address_rlc` is needed for lookup of the storage change).

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
Branch 0 | Branch 0
         | Branch 1
Leaf 1   | Leaf 2
```

`Leaf 1` in `Branch0` is replaced by `Branch 1`. `Branch 1` contains two leaves: `Leaf 1` and `Leaf 2`.
However, `Leaf 1` has a shorter key now. To enable the verification that `Branch 1`
contains only two leaves and one of them is `Leaf 1` (with shorter key),
the modified `Leaf 1` is stored
in the fifth storage leaf row (`Leaf in added branch`). It is ensured that the values
in this row correspond to `Leaf 1`.

<p align="center">
  <img src="./img/placeholder_branch.png?raw=true" width="50%">
</p>

In order not to break the layout, a placeholder branch is added in the S
proof. This way, the leaf S and leaf C are positioned one after another as in other cases
(where the number of branches above the leaf S and leaf C is the same).

To make it simpler, for the placeholder branch its paralell counterpart is used (when
S branch is a placeholder, C branch values are used as a placeholder; when C branch is a placeholder, S branch values are used as a placeholder).

This way, the equalities between S and C branch still holds (constraints are
still fullfilled).
On the other hand, the constraint for branch hash to be in a parent element is switched off.
Instead, the hash of a leaf is checked to be in an element that is above the placeholder
branch.

<p align="center">
  <img src="./img/drifted_leaf.png?raw=true" width="50%">
</p>

Let us denote by `Leaf 11` the leaf `Leaf 1` after it drifted down into
`Branch 1`.

There are some further equalities to be ensured.
For example, `Leaf 11 key_rlc` needs to be the same as `Leaf 1 key_rlc`.

Note: `Leaf 1 key_rlc` is computed using nibbles in the branches above `Branch 0`,
using `modified_node` of `Branch 0`, and using the key stored in `Leaf 1`.
Once `Leaf 1` drifted into `Branch 1`, its `key_rlc` is computed using nibbles
above `Branch 1`, using `drifed_pos` in `Branch 1`, and using the key
stored in `Leaf 11`.
If `Branch 1` is extension node instead, the computation of `Leaf 11 key_rlc`
needs to take account also the extension nibbles.

Further, `Leaf 11` hash needs to be checked to be the same as `Branch 1` child
at `drifted_mod` position. The only other non-empty child of `Branch 1` needs
to be `Leaf 2` hash at `modified_node` position.

In case when there are two leaves in a branch and one of them is deleted, the scenario is reversed: C proof contains placeholder branch.

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

In case of a placeholder leaf, the leaf constraints are switched off for the placeholder leaf.
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

In case there is only one leaf in storage trie, there will be no branch.
When the second leaf is added, the branch or extension node appears.
Similarly as in the first case, a placeholder branch / extension node
is added. The difference is that the hash of the leaf in the S proof is
checked to be the S storage trie root stored in the account leaf rows.
The hash of the added branch / extension node is checked to be the C
storage trie root. All other constraits are the same as in the first case.

<p align="center">
  <img src="./img/one_leaf_in_trie.png?raw=true" width="50%">
</p>

#### Case 4: No key in first level

When there is no value stored yet in the storage trie, a placeholder leaf
is inserted as in the second case. Here, instead of checking that the hash
of a (placeholder) leaf is the storage trie root stored in the account leaf
rows, it is checked that the storage trie root is hash of an empty trie.
Thus, placeholder leaf is used just to not break the circuit layout.

In the C proof, the hash of a leaf (the first leaf that is added to the trie)
is checked to be the storage trie root. When the only leaf in the storage trie
is deleted, the scenario is reversed: the placeholder is in the C proof.


<p align="center">
  <img src="./img/one_leaf.png?raw=true" width="50%">
</p>

## Proof chaining

One S/C proof proves one modification. When two or more modifications are to be
proved to be correct, a chaining between proofs is needed.
That means we need to ensure:

```
current S state trie root = previous C state trie root
```

For this reason `not_first_level` selector is used which is set to 0 for the
first rows of the account proof. These are either the rows of the first
branch / extension node or the rows of the account leaf (if only one element
in the state trie).

The constraints make sure:

- `current S state trie root = previous C state trie root` in the first row of the first level
- `address_rlc` is set to 0 in the first row of the first level (in the account leaf it is set to the correct value, elsewhere it is not allowed to change)
- `counter` does not change except in the first row of the first level

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

### Account create lookup

Because MPT circuit allows only one change at a time, there are three lookups (`nonce`, `balance`,
`codehash`) using the same `counter` needed for the account creation.

```
lookup(counter, address_rlc, nonce_prev, nonce_cur, is_nonce_mod)
lookup(counter, address_rlc, balance_prev, balance_cur, is_balance_mod)
lookup(counter, address_rlc, codehash_prev, codehash_cur, is_codehash_mod)
```

Default values are to be used for `nonce_prev, nonce_cur`, `balance_prev`, `balance_cur`, `codehash_prev`, `codehash_cur`. Note that `prev` values are not important, we do not need to prove the correct modification of the trie here, we just need a proof for an account with default values to exist in the trie. Thus, there are no constraints for `prev` values to be default values.

Also, there are no constraints for `cur` values to be default values, because the
correct values are implied by lookups - the lookups (default values passed by arguments)
will fail if there are no correct values in the circuit.

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

## Geth proof examples

## Examples

#### 0x9cc9bf39a84998089050a90087e597c26758685d

`curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getProof","params":["0x9cc9bf39a84998089050a90087e597c26758685d",["","d471a47ea0f50e55ea9fc248daa217279ed7ea3bb54c9c503788b85e674a93d1"],"latest"],"id":1}' -H "Content-type:application/json" https://mainnet.infura.io/v3/c63a7f71839b43ae957af14112d62c68`

branch

```
0:b68ba00b34a26d815df967f32a092bc3f743221f96719488ba8704a1fd3ca53a
1:7bd8e54142bfffd1a2bdef6fc48d8bc3773309f41df47bd2197ef3d321e82a33
2:f782c5139e831825ebd66635b25912ef13100b91c26fc14a16a5f44e0f932ea5
3:50dbaacf62d90933cd6ec229878bea382327cbfca06960ad1bc1605cb8ccb0aa
4:31b6a514e7a50c30831c2b696c508ec2ca26b52a4dba3edeecc96587eb8e63d6
5:c1929b964bccb36c23fd9e32ad3d21f1d441f20319515dab7cb445f81ace0d57
6:61e9af0efaef3eadfe4e1ed73151960f89fcdf43e80e47c3f421cd067e7d4f50
7:42b0a342c41bf579d8e731cd69599f6db732a2e0e6a3651ea75a6417d5a8ef47
8:cf6b4ea97065ac0a3ab2df9271bbb66ff705ec2bc6695338e3cbb0a6b75f59f5
9:b0196336d1c91cf026aad4eb2a8595ea50490720de1c220b70d0a45a82ba903b
10:3171a87c75fff6fc351c8138c0a40e7b9263ecc725507a340f881ab643639f7f
11:f1ea9f60510a8f77db2ba5b79cc177a75213f5ee8827094c0f7ca39c7ce6e2de
12:83142674e48e37996db60cbea0480434890fd1874540be8ba21e16ffa9cfacf1
13:7ae7ad3cb960c60a585eaac142af40669c519df8127b0276f953f8a4840c9383
14:00e867085187657cab0e15340300fd8e5397ea632a3fa0cf70fa7cf6aca6da33
15:b54830fc8d74779bb9101eb047d4201837fe61347d4f559caf2c8196905f18d4
```
branch


```
0:16880e1a2996cd483e3199a051546214505b077c725adfce15079756da3da54f
1:1e4e5e1cefc4a795d3b71887ae7f57634fbf3045dd92cd6c545eb23b6a2118e7
2:46b62203ba4e12e61d97648da106dad55c6cd7fe6d36c591c2974546ee8f6888
3:95833d354103e370bd72363304503e42afb172a724480edc098e6e0a081761b8
4:75dd73673889b4067e513290af9ae3a0d2d4a254e311d603cd889ad32debfa9e
5:3af2a47ae67e2030a1c3189e91fecd1588484f56080f26ce32fbc144535f4e25
6:40dfc4c386a792f324214b7b2d8724b0fdbe4331abc9adf91ec6ca4c97745834
7:ccfa6473915693c1d7053f0bcdca1803a417d0b35d290314cc9354363d4f051f
8:c4eb0688c1244566649b81e97dc48aa4fdf2eac0a01bfe61021f740da79c5049
9:5ab33c5428c64d83bc9ee6356d1882c99a87638d936a50d5e9ac57cb17729bb2
10:1ed62a79b3625b7d67c41ae0d7bb8df633b8b6a81b2b82d86e990f6e5badef81
11:ac9a139d2802332338f3f43ca488e2ae49452736485e2d79b1c8a185ddfb5676
12:11bb682b676767bc4fec4c9f40dd1ce3c8ee810c5e0c54b1bcda61c04effa5d8
13:bf0a9e3241411a308d25c09d0f5d1b3945cea8f32b64db1def53bb41ec5c813c
14:410fc8a29cc20c2ff0998f83e5d497e74964a232d4e29f9926b3214b1e87ae0e
15:e25937366cde5200be5bf41c04ba04296d6e9fa8ccd2c96651761ea54c347a4f
```

branch

```
0:95a87e4774979bcfb04e10aeb68088ba923adca62a9b9a25eebd154b5b84ffff
1:abbd9509794bdc47a073f71fbe1ba55cfc7cb63256c9494b31cf65df55700621
2:3ffc0d941e7cdc437bcc883437b15a57af4502e6491fc9636e0156c62dfd93aa
3:fbb24db1daf62f47980295a770a371f031b64a65f197cdeecf8f07eea9a0a146
4:5abeba9d589e0465de6f56f33c71c538cbf73b80e33fb1e2818749d1144ebbe6
5:ca7cf8254f8ecab5769d7b5bb019a2d4f5dedfa0d13ae565695e4e697f13c8c4
6:3d17f1dfaf64d5d192cde8ee0dd6c96021a3702646d277ba49ec63980e1a2f80
7:826cac7d2aead31a4b5d0cb98335f40aa7443094e702219c6ec8d5a2b85bd901
8:b29e4c8a5883170bb66cad24da11510618daa8ab5064e910922b576b497f12c0
9:7ad68eb9efb09b1007ec29334bdea367b880f1e9ee98d4c28b24122e8c7deb45
10:a350fe907152b3268298d0bbd522bbef2a24312860954870ce8f41155edb1d2d
11:aedb44c8dc55ee7fc0189397aa3f915a1a6292ef6ba24aa842a546f89e136f3f
12:e42d966dc07cd5db21dabcf5854b95cee5bb4ae87138ca9f3fe3d58af1b4fc50
13:fe45d331908eb5146160a2f1bbbeeef0a27be50c62c69bfe64b21e93285868aa
14:a15bfec15c18b8ba8042abe78424bb388738c9b4a0837e6852a282bc6c111a53
15:9c60d298ffee6af737cd1cc5e5e83b1ad45153a36187a381138621c5eecd7795
```

branch

```
0:e2b23cd5d258e893fcf514947f7b59dbfd87ee1638c105c735fc7bc8962cd02a
1:648b4f69d5156376c2bfce0bdabd86d788b6f9665fe2533f1bf1114736cda03c
2:fb5a971021f7bc2bfcd0b38d96b6c6ff05adb1a53d4673200afdd30653d7ff1a
3:1825b21c47b2b99b591271aa6b30a0b67913ff090d1d34f4a248c62708e9b59b
4:460d6cc60a6a4f2de9dc415da00c24b48c2daa32969bd4e203112712619a8755
5:57d20794515a2523e93a66bfe5e80fbd521dcff1d7c91dbc10f0172b0da351e8
6:28d1af601ccd2f58dba74d7473d8ab015eaecf7cee781fd149149f431900da07
7:c5bc26eb06d320fbc24c225169a2d8a1ff2dc088ed211e6eefda2558d5f740b4
8:6116cec11f70edd5568e8d79718fae2629872bec2192d5a588c19485459c6e38
9:6406e4b2f1f59856314ef0158eef3afd79085fe4f6993f4b22108bc85ae86d46
10:4e621eb0743bd6f02f148e0eed4fb35a153a59b8dff95b94ac3b8adc7e3902e9
11:721a67c478ddaa6648f8ab37cc58bae029b05a47ecbd8a6ce2567ef346c64931
12:517240054bec815fb14a9a2f125de84d5baa9589ec95099d2408e40a2eb3afcb
13:5987533ecde4cfd043c6f229aa4103406d2d63d7a968fe38e64396d4b5303aa2
14:de7ea2573ced174d9d74f57293ceb1d28b49e0be33cd0b4357369621a39c902c
15:a17fa9bf11c662f12c2d502b2ce5e210b4ecee7a9eeedad9f49217ddcb671b93
```

branch

```
0:bfc3bdf96c5f789e600ed9a0c5a85a453222d9efca07aa62e1713bd2507d6257
1:3706279aa3ca8107b1d695a30632bf0885e53c5200a2b757d6a9c180028d8893
2:06868a27247b91fdc8a00b547790c65faf26c09a550d5d70804d5f1f2d8a9989
3:d0a567de33477ed3598c04e37525e4f8d853c3479fbcf26c65f2af2f7834b09f
4:f8896498c812a2d1dbadbc59be632bf93088d11f6e325cfef956ed9a9c4fc3f4
5:193b5f414c2b19d3bd43937ffae1b66ade621064af5bdf8935721f4a611838b2
6:b876f545aac3c3bea38ac227c7f800ccec3eee51bfefbf53c40acf96d1d38342
7:53396bfbb9765eec0242195f65d1d3902135a5a6027a26915f7c450896811e09
8:02349fb46f39692157f621099b11f712a847cbd5630b8111a1fcb4b712200870
9:99f16bf1d649c62b07502143151c708a348c81050bcf8eaacdfbc598ba3bedf7
10:760707bbc6a076442b287cbd2914f346289aede5b51367719cdc0f7afaa9e626
11:115038c120aab2cb6521b57565b715bd795bd0af8842fcbe779f8369ea54688c
12:1a4c8c8340b6e1eb001e142189fff34a86f7cb3df0cb0ef9710a75b15bfb1fc9
13:9da27a67e9de6d2b43d79a111331c3033dddd4bc1793cc884a4d488d85124b74
14:805926be9fb6706b26dfbf39b195ce280ca54f4346e479dc8609ba6f0eca0ee2
15:49a6867829bd59a87e3b423a46bbc0d56402d5718a8c10b794efb8fa2dc617e9
```

branch

```
0:25562195a181ce2cd695cb301cc8da8ae74646a8d534949340de978828c942a6
1:ecafe0dfdc8f765b1b87eab8c4af00b30e2b932f979ce3a794f57ade3d16e896
2:636e8214f41365b44ad8ace2236129abc7174da2e6f3f197757f350ce7669226
3:10e58fb22ae9f20bfe559749fcbd9068285e90d9c42548b07a53d8c438d0bfb1
4:e89db2f065c7f631054f9656a69b83bb4a86df0b8d25ce02e859f58c2d06207b
5:db2f4216e16fb9cb8147952ed07ecfef13e60b5fa2fcdb62b2da8a48c9b5a733
6:4b2d4a7b639dd06dd023d367f443c64ab39ee8c9bcd4cd25b702ff9d68f18a0b
7:6a9c675f4d0f9832a6a7371701fbac3b4fc4b89ebc5af7e70505d4b81435bfe0
8:fb3edc63e8609d5b2a74e54c76b127b5b2c931daddd36395b3099d17231d82a9
9:2f0a0dbf18e2d6aa9bbb2601c63b4e8b66b93627fd702bf76dac0db8ed2f58c0
10:7e2431c25bb1645f698f9ef6f0591f1ece0ed0e012f19e0d7ed7c0ac3303a322
11:d10ab1b7e4ddadd44cd30474492092832e14b9fc4f069aaa22b7e8887b3fb02e
12:60a68f07c313703050cecccd01d181c89496920fef7add95e9c175ed92cccc4a
13:ce51a7a0ecdc4d8ca8e2e00407557780d3f7fe79dc7fc4e84fa3a2b6df98868b
14:fdbf2c5bff1e1fa655816f5e8a9c2b21322cd6129ec5401f89502188c40a4c0e
15:cdd91fe59922cca4c51e63bc7725f90e2de22209ae628beed3fb69774eab1f88
```
branch


```
0:50c8902986a361aa24d61ba444a4bdb58cc24a1cc75cba18cb9f4cc0dacfb277
3:4735deb634d0e011275aa5b310ae4a15a55e975149b069792191efb67df42915
6:01acfcceaef1d701352ff78e60b2dd97957a1c753e67538c3571c2557a00a283
8:d5cc493de801f25709a0d87a6599b0ed5b01fd5869f08f96f6b838dd019cddb4
9:37fb984c6c1e14e4e1d4e98d6d45cabe83f878f3a36d9435a5cbce1b3634916c
11:e6b7500ebd2b6b90e2c0c2208e5e7a85e8bd4b7392844d81864ddd961db07d94
13:119a8f20df7c27e341cfd505ee69f2ffbc33f4ce564094abef839b058db0ff65
15:ed5e5306b58a41180bbdbeabb3d2a18b9c6ba594cac9dff3fa62632e931636cc
```

extension 

```
0:16
1:e886040251f67ebad1399818dd16d3879e7b4ce836ccdd16562e640bd7462c47
```

branch

```
1:d12e19add3399af92b890ec9eeb5c9b9152f093d20600fe587e6472314a37afe
12:315279f9bc0eb2ac0827d79d4b2ede9acc71c485fd3bf993c783e00c5b76fc4e
```

leaf

```
0:32375ca53a40019b1c64f2fb4cfbee5ff546cde64bf4bee12a4c0088
1:f8440180a0c14953a64f69632619636fbdf327e883436b9fd1b1025220e50fb70ab7d2e2a8a0f7cf6232b8d655b92268b3565325e8897f2f82d65a4eaaf4e78fcef04e8fee6a
```   

decoded

```
0: 01
1:  
2: c149 53a6 4f69 6326 1963 6fbd f327 e883 436b 9fd1 b102 5220 e50f b70a b7d2 e2a8
3: f7cf 6232 b8d6 55b9 2268 b356 5325 e889 7f2f 82d6 5a4e aaf4 e78f cef0 4e8f ee6a
```

#### 0x000000000000000000000

branch
```
0:307fba09f3e9867e0b4fe394bbcd24d4013ba40b9639c6426bada55a2c200993
1:ae6dee8ac633cdc1a97ab07b8de3229e85962ae93778ef73a62d2df766ff30be
2:548c4a387f320fadc49f38d9c61c043b717e2fd020ecfc75aaab980ba74e7475
3:699f7c25b861c30b3283547c681c77031184db1ad0f78b95cb309daa8d353a44
4:4d77307d7d58393f7c34731d0f5c5f20680b3cb4aafb5d8c6ebbf5edd154bf3f
5:1c5a3ce9d4809487298b7914ed9475a8a16639bc204291f149ecbe6f0e258bd7
6:b97a9736c405bb5c7cbb0c5e797df7c3b3602e80b994d7b60418c18ef1a80f9a
7:3a03ef17f5428350b66ee1cf70729e7d8046ed80424aea2a710e283d0b576600
8:33b91562d04df182e39fe7c84fb76e92b2f6feef89647f5d7ac3326e9dc4417d
9:b56acff1342cfaa6c62626aba355ddc2cd3ce36a44cd289425567135b5e05ec0
10:4f2ebab3b7b8fa476d649fadd35c15cd955773ee6aa0b6ddbc991aa98a7411e0
11:59caf2bc71f5db69aef4c39eadc698b36d810c2e249f72b89edba96ae57adf67
12:5118e6d627de78c0f307f4d126c13bd01b0e9574fe5c4930a3e656f59077dcde
13:e81668785c5b3869245a9e3c872ab3d7d7f4f4d3a57cc41315163f4a2f6c7c73
14:5f6875aaf748a291ca22227083e2fcc1d0d8c71b54ebea1f55569724f069e40c
15:8325960c953ea9e9c70d7de3cf54b325f7f0c7853fe456ce2ea58601a009aa55
```
branch
```
0:92ed1bd39d53ff718195666f1026bee8e75e968767e64909079f9d5eba4d0cd0
1:e884474fa7c9e9adba686e7de9acc05b551ea68446abf6900ab635514b4be02e
2:64383f7bc092f11b89946d023a92de9f26523701cfb7eca66628732d1831550a
3:ab2733856cc4e5711bc1bf87a7b70dbdb6e981360209908e6ab590767c719171
4:7945e2bfd897bc23e54e61db2372bb2ee64ea09dbe7fe832bc20f1180e354f3d
5:cbbe10127dc0045d8d02408759ff1f98d5586c262c410568efb1278a35ac2c79
6:9d55e5d19b6e936ace18dd504f681b0b6533d476f8ae7fdb204698326ea7ffef
7:ec9ad5961211c2ff01d1685f628f5d8230ad3e9722a3d5959a6dea622eb5d0c9
8:64189119c00add9d140383dc06b55f935b4594c84d01dd24f298f176696b5716
9:42f9e5a5c22bca81b30ad015652ddc9534cfd288b7eb6c585a05c504018ab360
10:2a290dcbbb8c23e827c0b898bd957b1ed6f514087a7ede579c30cd673cd3bcd9
11:da60bf1f4d5fe830722c9056c10a1d0f76989b4f24c788e54723f15eaba4ba46
12:4f840fa5bce9f0caa55fcfc2ddea852d5103221106eeb81c73ac0cc4efcdea58
13:1d9ce00035049e577b5e67513fdb0cd6b244404d51f8cb96e72924689a0f6fe5
14:85634c34b7e589f59726d20bf7ef2fe87931f2a309a874ea126cd5820e5b5b6a
15:5b4b246febb38a50a59032694cf9f4d4dd09e0a72e7488b3153d41dca8244831
```
branch
```
0:ecf57c84e14e76346166a53ea7a9c8bfd41b9489ab770c2cfcd30c743750b13c
1:12e4a51c2173bee474e2c508f42c6b3b1db1e7c2d7c4f7e6ac7262c6d31e2063
2:d2767e003c4dd0992f1e3033cec3cde39b4e074fcaa588939f8cd1547c858d7b
3:e26e9fa7d3891769ec28c6d4e00accc045aa39558f86e07170bf5a71d3f9e99b
4:92c0de5a025188b937ce023ca6ba6631a190d316b6ad697fc03bfe33fdef16c6
5:9f39515d7c1c74795318c80e69f7c3113efc5611ff1e98bbd08d3f3c9fde4812
6:d644954e4f07f3e3343ae42af78ed19f5bf7cabbf7483c8d2439a25b838d1bf0
7:a3922e74fae1e69a1b139fadd2a050fe7bc7ac2e7cfb7f22f55542e054d7ba9b
8:0146ca0191e7a3286621949b5ab82544780202672b7dc1ad726efcfdd5d5e616
9:5bd972de5b1763d2118a4f900de3005190d3318b40ca95259b50f5ade2973004
10:313a19f2b5a6f2a335e450c45020349bc6fa15534d08178836dca978b9d37636
11:1fa72c2263ab22c81bad60d4619da83267afa53c18eb3c2deb262218240a1ad5
12:ec9a7d724fe2917f8eefeea6e546beeef5f096ac325b53f9becf9a856af9021c
13:f49c524ab3fcc60beeb37686d2df2c6edff83f3da84608a3344a6606c75b5bc2
14:49a4cc463854845f4055aebdfab448efe482d7a66533ef849e1102be495c7cb0
15:238e3e1b5d69e48946954d15d230dfa5cc13ae61b3313cc096e2411fe1e98c02
```
branch
```
0:525146277a9bea45eeb6426a312b464971dd4bce29d2a91bbf20a99a7e7de39a
1:19e4f87e8ed374eb57ff4ea98fb5ba47c87730484e271939c52b5899c052e798
2:2b35c8065ee836c0f52c0cde0944619dba6bd6d4b1ceaf7b99cd95ccbc8c6393
3:5ac573d737043b0a04127ff6760aef4660fd03a6bbf5e7e38a1607dcd77265d5
4:c73402e0ed34121759400e1d5129d1ebce0bfb0a0ffffed78318931d1bf71c49
5:d7e7082befb32b9dae14d586b166d7afecf8ebc131ebe5184063597ac2653579
6:64bd64734d39036966f096a2a454431cca38ca395f8125f8e0b6286947f594c5
7:b056f2ea579d00ab54861d851db411370b57fe35175c7b200a6520f0415fd211
8:ad162dd4156a09b5c67e19a00f2f444fadcda11e36603cd1e6c24d7125dadf4b
9:704a7e931d487e63b49c246104497ba35c9b339e09bfb64db393e8c11a795674
10:eb5a5d23753b7e39db60479705311b0d9047add86607a6990ef71182b947c47d
11:cd13c6b6d4451bc606bbd645eca809274d9c9b01c1a29d64dce06bdcf9a1ce2e
12:1cb44a37334f36ae83f084626c77a75ad7eee6c788c279fb926155608ca64dd8
13:fc89e2f1d43e148a7734f4717b5784534b60fb8c716e1ae4413231678bf32f28
14:2517f58fdfc55a2e72c68ee596e64e9471b5c0a978a822b34c07a2e9b041514d
15:a5ac940eb2410329a48108f790d188f91ec30f4dbe7072c8ec7b61de0f32d4bd
```
branch
```
0:6c0cda34feda8e314606fc19a014f16dc343a40af7a49842308dd86f2951bcf4
1:c0ba816f9019bbffd02ab8fdb3298fc6e1edc952eb137dc36cd7b3f7910163f9
2:ff28e4a60358f3af7d666bf45e533a4b5ae1a78dd65e10ba5a9e10fdc1298ce2
3:e1654c217784078a0b65f5c5f6799945834456969cd5516f6d0bb436c1dc3668
4:6ad99ab9498b77b21a9fadfa2482240bddc0de4fd2714b42c9b11cc6be0b8a19
5:eb4ffc250a6d9a598d18e5bcc2b0481f222c8633ba15f0a702d9b4dc4a891767
6:9b583a41c3932eb2981b12a349057cf3f69d97cb5ca861467dccc469cb885207
7:3a53d870f6bbf94e69efa0e69dcb79e7c81e0b3cd4e4f0ddf50bb47bcdf00d2c
8:2b2c5adf4f0bef2308f13ddf6bb389283a44d835224180abce1c79bdc3682082
9:c5ac729fb46f91b2a4906f5470815e57af05c5d1b2a32ea435892bf9ccb0fccd
10:ce2821b6c50e29cdc6438a2b7c99f8fc4a39a184b0c4daa33d9f4baf6ee84741
11:70fda661f16cd8b8bc41f309a17cec379040755928f7e9d2c503319af81a6242
12:88aab3bfd4218726acdaf7c75379d45b88b5cbb8af667af9c693b1e065998132
13:fd65287e8d2c46115b6d675ea5289a5b629a38b631eb933f09c56d6b10352284
14:92bc0e392dd73425548e15ccc8b2d6b65edc6943f3dc439bbf6d4e0e1d425456
15:a264fc1b7a5a35b33b3497a03fe087e959dcdcde803fb48cc494750c4b0b5b8c
```
branch

```
0:6a106f157b87105a295bf64cd60ca92e000627a452bdf62a4508656398cc8464
1:c3c2ed37b96d3190f04afc9042b508f311f2f08491df85367d7725178b29509f
2:1d4847cc13f7740cdb19df5aeb6435a1c1e601828fb9b1ba51161b51e56a2612
3:c92a42a712309deaeee1e350dc1da047581ddad92196d6f0d1800bec9f826c45
4:1fa72a281e7d31c0f3b6a2833699887a66adb3c1355c17e19255db927034cf76
5:d8d9e80c8014f52f03499cf22f86d158613fa4203802fef981c60f783afe9408
6:f5afd490d2794ae2740b91e906924d694287fdc3f9f8f4756145808aa8481d8d
7:4d994f63b00c21ec690a340028f44f272a851710faa3a82f59c8450b2d5c5521
8:61db2906bb6d9539df7b655dada808c945590aeedd514eda2b0f319769a930ee
9:0cc694cc46793187a9349aa139e38543b0aa89a1407a34032cd7cdbbe17f8918
10:438ac4c7a908b8e238550b967abcce55ca3e2ebaee5f099d034547487ee4f894
11:e434d71446bc0e7e57212c6e9c51404aeaef72793a78573d11b5b52ea93364ee
12:62c29a97efa09c83e84ac1dee8f2ff78e7cf2fa5f4fd7d4a03b2c1b52a6afcd3
13:f2ec9b17f9c92f3690332bab50727866ce1e1e6f58309fd177111dde749615ce
14:3768dc2f979daec77db519b61c2629389fe2f9f71940d04fc6d5af2f6ce5f2c7
15:ec235e0a726169c95b88277ecf69b0b04b5253d5fe4e6cfa58534029a42d75b3
```

branch

```
1:3464dee21bd9b7f1712c25a7bf48517d93f6cd02bc5e069e85ca98eef103792b
3:ac233ce7e7018541d154a3abf88a2d3d564777b116c94fec994ce36d0ae1582b
4:fd874c87366c0aaaf7fccf6065684b0745c3dcb1632d64ebb023cfe15512924e
8:2073bcfe0a91dc4b71e13226cefc82d938a69b86d682b838f1db53f367510f8f
10:40c3c8f7a9522d6df5c0028d90d360f73c5169b4cf434d95350beed43e167390
11:b4e5de1583ca776461aa87a4dc220a20bb9a223616c702e28161a865ee11a9c2
12:bb39d214636f90c18e92ff7d05f905a72018bc93dc11899124a3d976779a056a
13:598f8e0f6c6ea52b62e04c655de5e5494597c2902078b98091861dd0bf237873
```

branch

```
4:6cb96634150a4bf19ad1cd1d29ead274d327b6c478fe4624570e3b7f848fea31
7:5be9025d68d4b037ae9fbff367a82463eda2cdd9b66871b48ca7fca2095cbd29
```

leaf

```
0:20ae81a58eb98d9c78de4a1fd7fd9535fc953ed2be602daaa41767312a
1:f84e808a0269fed86bdad0f2d9eaa056e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421a0c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
```

`f84e808a0269fed86bdad0f2d9eaa056e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421a0c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470` value decoded is

``` 
0:
1: 0269 fed8 6bda d0f2 d9ea
2: 56e8 1f17 1bcc 55a6 ff83 45e6 92c0 f86e 5b48 e01b 996c adc0 0162 2fb5 e363 b421
3: c5d2 4601 86f7 233c 927e 7db2 dcc7 03c0 e500 b653 ca82 273b 7bfa d804 5d85 a470
```
