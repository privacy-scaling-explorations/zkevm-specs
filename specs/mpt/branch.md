# Branch

A branch occupies 19 rows:
```
BRANCH.IS_INIT
BRANCH.IS_CHILD 0
...
BRANCH.IS_CHILD 15
BRANCH.IS_EXTENSION_NODE_S
BRANCH.IS_EXTENSION_NODE_C
```

Example:

```
[1 0 1 0 248 241 0 248 241 0 1 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 160 164 92 78 34 81 137 173 236 78 208 145 118 128 60 46 5 176 8 229 165 42 222 110 4 252 228 93 243 26 160 241 85 0 160 95 174 59 239 229 74 221 53 227 115 207 137 94 29 119 126 56 209 55 198 212 179 38 213 219 36 111 62 46 43 176 168 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 160 60 157 212 182 167 69 206 32 151 2 14 23 149 67 58 187 84 249 195 159 106 68 203 199 199 65 194 33 215 102 71 138 0 160 60 157 212 182 167 69 206 32 151 2 14 23 149 67 58 187 84 249 195 159 106 68 203 199 199 65 194 33 215 102 71 138 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 160 21 230 18 20 253 84 192 151 178 53 157 0 9 105 229 121 222 71 120 109 159 109 9 218 254 1 50 139 117 216 194 252 0 160 21 230 18 20 253 84 192 151 178 53 157 0 9 105 229 121 222 71 120 109 159 109 9 218 254 1 50 139 117 216 194 252 1]
[0 160 229 29 220 149 183 173 68 40 11 103 39 76 251 20 162 242 21 49 103 245 160 99 143 218 74 196 2 61 51 34 105 123 0 160 229 29 220 149 183 173 68 40 11 103 39 76 251 20 162 242 21 49 103 245 160 99 143 218 74 196 2 61 51 34 105 123 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 160 0 140 67 252 58 164 68 143 34 163 138 133 54 27 218 38 80 20 142 115 221 100 73 161 165 75 83 53 8 58 236 1 0 160 0 140 67 252 58 164 68 143 34 163 138 133 54 27 218 38 80 20 142 115 221 100 73 161 165 75 83 53 8 58 236 1 1]
[0 160 149 169 206 0 129 86 168 48 42 127 100 73 109 90 171 56 216 28 132 44 167 14 46 189 224 213 37 0 234 165 140 236 0 160 149 169 206 0 129 86 168 48 42 127 100 73 109 90 171 56 216 28 132 44 167 14 46 189 224 213 37 0 234 165 140 236 1]
[0 160 42 63 45 28 165 209 201 220 231 99 153 208 48 174 250 66 196 18 123 250 55 107 64 178 159 49 190 84 159 179 138 235 0 160 42 63 45 28 165 209 201 220 231 99 153 208 48 174 250 66 196 18 123 250 55 107 64 178 159 49 190 84 159 179 138 235 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 16]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 17]
```

Note that when `BRANCH.IS_CHILD` row presents a nil node, there is only one byte non-zero:
128 at `s_main.bytes[0] / c_main.bytes[0]`.

## Branch

### Branch S and C equal at NON modified_node position & only two non-nil nodes when placeholder

The gate
`Branch S and C equal at NON modified_node position & only two non-nil nodes when placeholder`
ensures that the only change in
`S` and `C` proof occur at `modified_node` (denoting which child of the branch is changed) position.
This is needed because the circuit allows only one change at at time. 

#### rlp2

We check `s_main.rlp2 = c_main.rlp2` everywhere except at `modified_node`.

Note: We do not compare `s_main.rlp1 = c_main.rlp1` because there is no information
about branch. We use `rlp1` to store information about `S` branch and
`C` branch RLP length (see the gate below).

#### s = c when NOT is_modified

Similarly as above for `rlp2` we check here that `s_main.bytes[i] = c_main.bytes[i]`
except at `modified_node`.

#### Only two nil-nodes when placeholder branch
 
 This constraint applies for when we have a placeholder branch.
In this case, both branches are the same - the placeholder branch and its
parallel counterpart, which is not a placeholder, but a regular branch (newly added branch).
The regular branch has only two non-nil nodes, because the placeholder branch
appears only when an existing leaf drifts down into a newly added branch.
Besides an existing leaf, we have a leaf that was being added and that caused
a new branch to be added. So we need to check that there are exactly two non-nil nodes
(otherwise the attacker could add two or more new leaves at the same time).

The non-nil nodes need to be at `is_modified` and `is_at_drifted_pos`, elsewhere
there have to be zeros. When there is no placeholder branch, this constraint is ignored.

### RLP length

We need to check that the length of the branch corresponds to the bytes at the beginning of
the RLP stream that specify the length of the RLP stream. There are three possible scenarios:

  1. Branch (length `21 = 213 - 192`) with one byte of RLP meta data
     ```
     [213,128,194,32,1,128,194,32,1,128,128,128,128,128,128,128,128,128,128,128,128,128]
     ```

  2. Branch (length 83) with two bytes of RLP meta data
     ```
     [248,81,128,128,...
     ```

  3. Branch (length 340) with three bytes of RLP meta data
     ```
     249,1,81,128,16,...
     ```

We specify which of the scenarios is in the current row as (note that `S` branch and
`C` branch could be of different length. `s_rlp1, s_rlp2` is used for `S` and
`s_main.bytes[0], s_main.bytes[1]` is used for `C`):
```
rlp1, rlp2: 1, 1 means 1 RLP byte
rlp1, rlp2: 1, 0 means 2 RLP bytes
rlp1, rlp2: 0, 1 means 3 RLP bytes
```

#### Not both zeros: rlp1, rlp2

There should never be `rlp1, rlp2: 0, 0` for `S` (we only have three cases, there is no case with
both being 0).

#### First branch children one RLP meta byte

We check that the first branch children has properly stored the number of the remaining
bytes. For example, if there are 81 bytes in the branch and the first branch child
contains 1 byte, then it needs to store the value `80 = 81 - 1`.

#### Branch children node_index > 0 RLP

We check that the non-first branch children has properly stored the number of the remaining
bytes. For example, if there are 81 bytes in the branch, the first branch child
contains 1 byte, the second child contains 33 bytes, then the third child
needs to store the value `81 - 1 - 33`.

#### Branch last child RLP length

In the final branch child `s_rlp1` and `c_rlp1` need to be 1 (because RLP length
specifies also ValueNode which occupies 1 byte).

### Branch children selectors

#### is_branch_child after is_branch_init

If we have `is_branch_init` in the previous row, we have `is_branch_child = 1` in the current row.

#### node_index = 0 after is_branch_init

We could have only one constraint using sum, but then we would need
to limit `node_index` (to prevent values like -1). Now, `node_index` is
limited by ensuring its first value is 0, its last value is 15,
and it is being increased by 1.
If we have `is_branch_init` in the previous row, we have
`node_index = 0` in the current row.

### Range lookups

Range lookups ensure that `s_main.bytes` and `c_main.bytes` columns are all bytes (between 0 - 255).

Note: We do not check this for branch init row here.
Branch init row contains selectors related to drifted_pos,
modified_node, branch placeholders, extension node selectors. The constraints for these
selectors are in `branch_init.rs`.
Range lookups for extension node rows are in `extension_node_key.rs`.