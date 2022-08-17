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

We have:
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

Extension node contains two things: extension nibbles and hash of the underlying branch.
In our case, the extension node would contain `[1, 8]` and `Branch2` hash. Note that before `A1` has been
added, `Node_1_15` was hash of `A`. After `A1` was added, `Node_1_15` is hash of the extension node.

## RLP encoding

The RLP encoding of the extension node might look like as follows.
1. Having only one nibble in the extension:
```
[226,16,160,172,105,12...
```
In this case `s_main.rlp2` marks the nibble being `0 = 16 - 16`. `s_main.bytes[0]` denotes the length
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



