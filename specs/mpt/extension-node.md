# Extension node

An extension node occupies 2 rows. Extension node is an extension to the branch and can be viewed
as a special kind of branch. The branch / extension node layout is as follows:

```
IS_INIT
IS_CHILD 0
...
IS_CHILD 15
IS_EXTENSION_NODE_S
IS_EXTENSION_NODE_C
```

Contrary as in the branch rows, the `S` and `C` extension nodes are not positioned parallel to each
other. We have extension node for `S` proof in `IS_EXTENSION_NODE_S` row and extension node for `C` proof
in `IS_EXTENSION_NODE_C` row.

Let us observe the following example (similar to the on for
[account-leaf.md](account-leaf.md)). We are adding a new account `A1` to the trie.
Let us say that the account `A1` has the address
(in nibbles):
``` 
[8, 15, 1, 8, 7, ...]
``` 

And let us say there already exists an account `A` in the trie with the following nibbles:
```
[8, 15, 1, 8, 4, ...]
```

Also, let us assume that the account `A` is in the third trie level. We have `Branch0` in the first level:
```
           Branch0
Node_0_0 Node_0_1 ... Node_0_15
```

`Node_0_8` is the hash of a branch `Branch1`:
```
           Branch1
Node_1_0 Node_1_1 ... Node_1_15
```

`Node_1_15` is the hash of the account `A`.

Thus we have:
```
                              Branch0
Node_0_0 Node_0_1 ...              Node_0_8                 ... Node_0_15
                                      |
                        Node_1_0 Node_1_1 ... Node_1_15
                                                  |
                                                  A
```

Now, we want to add `A1`. We cannot replace `A` with a branch because we would need to put both,
`A` and `A1` at position 1 (see the third nibble). We check how many nibbles from the third nibble on
the two accounts share and put these nibbles in the extension node. These nibbles are: `[1, 8]`.
So we have an extension of `[1, 8]` and then we place a branch `Branch2`. We put `A` in `Branch2`
at position 4 and we put `A1` in `Branch2` at position 7.

So we have:
```
                                             Branch0
Node_0_0 Node_0_1 ...                       Node_0_8                                   ... Node_0_15
                                               |
                           Node_1_0 Node_1_1 ...             Node_1_15
                                                                 |
                                        nil nil nil nil Node_2_4 nil nil Node_2_7 nil ... nil
                                                            |                |
                                                            A                A1
```

Extension node contains two parts: extension nibbles and hash of the underlying branch.
In our case, the extension node would contain `[1, 8]` and `Branch2` hash. Note that before `A1` has been
added, `Node_1_15` was the hash of `A`. After `A1` was added, `Node_1_15` is the hash of the extension node.

## RLP encoding

The RLP encoding of the extension node might look like as follows.
1. Having only one nibble in the extension:
```
[226,16,160,172,105,12...
```
In this case `s_main.rlp2` denotes the nibble being `0 = 16 - 16`. `s_main.bytes[0]` denotes the length
of the following string (`32 = 160 - 128`). The string `[172,105,12,...]` is hash of the underlying
branch.

2. Having only one nibble and the branch being shorter than 32 bytes (being non-hashed):
```
[223,16,221,198,132,32,0,0,0,1,198,132,32,0,0,0,1,128,128,128,128,128,128,128,128,128,128,128,128,128,128,128]
```
In this case `s_main.bytes[0]` marks the length of the non-hashed branch: `29 = 221 - 192`.

Similar example but with more nibbles (note that if extension node contains up to 55 bytes,
`s_main.rlp1` will be up to `247 = 192 + 55`).
```
[247,160,16,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,213,128,194,32,1,128,194,32,1,128,128,128,128,128,128,128,128,128,128,128,128,128]
```

When the extension node contains more than 55 bytes:
```
[248,58,159,16,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,217,128,196,130,32,0,1,128,196,130,32,0,1,128,128,128,128,128,128,128,128,128,128,128,128,128]
```
In this case `s_main.rlp2` marks the length of the remaining stream, `s_main.bytes[0]` denotes the
length of the bytes that store nibbles: `31 = 159 - 128`.

3. Having more than one nibble:
``` 
[228,130,0,149,160,114,253,150,133,18,192,156,19,241,162,51,210,24,1,151,16,48,7,177,42,60,49,34,230,254,242,79,132,165,90,75,249]
```
In this case `s_main.rlp2` marks the length of the bytes that store nibbles: `2 = 130 - 128`.
The actual nibbles are `[9, 5]` as `149 = 9 * 16 + 5`.

## Extension node key constraints

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
[1 0 1 0 248 81 0 248 81 0 14 1 0 6 1 0 0 0 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 160 29 143 36 49 6 106 55 88 195 10 34 208 147 134 155 181 100 142 66 21 255 171 228 168 85 11 239 170 233 241 171 242 0 160 29 143 36 49 6 106 55 88 195 10 34 208 147 134 155 181 100 142 66 21 255 171 228 168 85 11 239 170 233 241 171 242 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[0 160 135 117 154 48 1 221 143 224 133 179 90 254 130 41 47 5 101 84 204 111 220 62 215 253 155 107 212 69 138 221 91 174 0 160 135 117 154 48 1 221 143 224 133 179 90 254 130 41 47 5 101 84 204 111 220 62 215 253 155 107 212 69 138 221 91 174 1]
[0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1]
[226 30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 160 30 252 7 160 150 158 68 221 229 48 73 181 91 223 120 156 43 93 5 199 95 184 42 20 87 178 65 243 228 156 123 174 0 16]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 160 30 252 7 160 150 158 68 221 229 48 73 181 91 223 120 156 43 93 5 199 95 184 42 20 87 178 65 243 228 156 123 174 0 17]
```

The last two rows present the extension node. This might be a bit misleading, because the extension
node appears in the trie above the branch (the first 17 rows).

The constraints in `extension_node_key.rs` check the intermediate
key RLC (address RLC) in the extension node is properly computed. Here, we need to take into
account the extension node nibbles and the branch `modified_node`.

Other constraints for extension nodes, like checking that the branch hash
is in the extension node (the bytes `[30 252 ... 174]` in extension node rows present the hash
of the underlying branch) or checking the hash of the extension is in the parent node are
checking in `extension_node.rs`.

### Extension node key RLC

When we have a regular branch (not in extension node), the key RLC is simple to compute:
```
key_rlc = key_rlc_prev + modified_node * key_rlc_mult_prev * selMult
```

The multiplier `selMult` being 16 or 1 depending on the number (even or odd) number
of nibbles used in the levels above.

Extension node makes it more complicated because we need to take into account its nibbles
too. If there are for example two nibbles in the extension node `n1` and `n2` and if we
assume that there have been even nibbles in the levels above, then:

```
key_rlc = key_rlc_prev + n1 * key_rlc_mult_prev * 16 + n2 * key_rlc_mult_prev * 1 +
    modified_node * key_rlc_mult_prev * r * 16     
```

#### Extension node row S and C key RLC are the same

Currently, the extension node S and extension node C both have the same key RLC -
however, sometimes extension node can be replaced by a shorter extension node
(in terms of nibbles), this is still to be implemented.

#### Extension node row S and C key RLC mult are the same

Same as above but for the multiplier that is to be used for the first nibble 
of the extension node.

#### Long even sel1 extension node RLC

We check the extension node intermediate RLC for the case when we have
long even nibbles (meaning there is an even number of nibbles > 1)
and sel1 (branch modified_node needs to be multiplied by 16).


#### Long even sel1 extension node > branch key RLC

Once we have extension node key RLC computed we need to take into account also the nibble
corresponding to the branch (this nibble is `modified_node`):
```
key_rlc_branch = key_rlc_ext_node + modified_node * mult_prev * mult_diff * 16
```

Note that the multiplier used is `mult_prev * mult_diff`. This is because `mult_prev`
is the multiplier to be used for the first extension node nibble, but we then
need to take into account the number of nibbles in the extension node to have
the proper multiplier for the `modified_node`. `mult_diff` stores the power or `r`
such that the desired multiplier is `mult_prev * mult_diff`.
However, `mult_diff` needs to be checked to correspond to the length of the nibbles
(see `mult_diff` lookups below).

We check branch key RLC in `IS_EXTENSION_NODE_C` row (and not in branch rows),
otherwise +rotation would be needed
because we first have branch rows and then extension rows.

#### Long even sel1 extension node > branch key RLC mult

We need to check that the multiplier stored in a branch is:
`key_rlc_mult_branch = mult_prev * mult_diff`.

While we can use the expression `mult_prev * mult_diff` in the constraints in this file,
we need to have `key_rlc_mult_branch` properly stored because it is accessed from the
child nodes when computing the key RLC in child nodes.
