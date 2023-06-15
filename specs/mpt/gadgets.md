## MainRLPGadget

To verify the RLP encoding, MPT circuit uses `MainRLPGadget`:
```
pub struct MainRLPGadget<F> {
    bytes: Vec<Cell<F>>,
    rlp: RLPItemGadget<F>,
    num_bytes: Cell<F>,
    len: Cell<F>,
    mult_diff: Cell<F>,
    rlc_content: Cell<F>,
    rlc_rlp: Cell<F>,
    tag: Cell<F>,
}
```

The field `rlp` is of type `RLPItemGadget`:

```
pub(crate) struct RLPItemGadget<F> {
    pub(crate) value: RLPValueGadget<F>,
    pub(crate) list: RLPListGadget<F>,
}
```

`RLPItemGadget` is an abstraction over two types of the RLP item.
An RLP item is either a string (i.e. byte array) or a list of items.
The abstraction provides functions `is_short`, `is_long`, `is_very_long` that gives
information on the type of the stream - whether the number of RLP bytes is short or long.

Furthermore, it provides functions `num_rlp_bytes`, `num_bytes`, `len` that gives information
about the number of RLP bytes, number of bytes in total (including RLP bytes), and
length of value (excluding RLP bytes) respectively.

Finally, it provides functions `rlc_rlp` and `rlc_content` which provide the RLC of the whole
stream (including RLP bytes) and the RLC of the values (excluding RLP values) respectively.

The cells which store information such as `is_short` and `is_long` are ensured to correspond to the
RLP byte by using lookups. There is a fixed table (with tag `FixedTableTag::RLP`) which contains the valid
options for RLP byte and `is_list`, `is_short`, `is_long`, `is_very_long` fields.
The table is loaded like (see `mpt_circuit.rs`):

```
let (is_list, is_short, is_long, is_very_long) = decode_rlp(byte);
assignf!(region, (self.fixed_table[0], offset) => FixedTableTag::RLP.scalar())?;
assignf!(region, (self.fixed_table[1], offset) => byte.scalar())?;
assignf!(region, (self.fixed_table[2], offset) => is_list.scalar())?;
assignf!(region, (self.fixed_table[3], offset) => is_short.scalar())?;
assignf!(region, (self.fixed_table[4], offset) => is_long.scalar())?;
assignf!(region, (self.fixed_table[5], offset) => is_very_long.scalar())?;
```

Both, `RLPValueGadget` and `RLPListGadget` execute the lookup to ensure that the cells have the proper
values.

### Constraints

`MainRLPGadget` ensures that the values stored in the cells `num_bytes`, `len`, `mult_diff`,
`rlc_content`, `rlc_rlp`, `tag` correspond to the bytes stored in `bytes`.

`MainRLPGadget` uses `RLPItemGadget` (via `rlp` field) to verify that the cell values correct:
```
config.num_bytes == config.rlp.num_bytes()
config.len => config.rlp.len()
config.rlc_content = config.rlp.rlc_content(r) // r is randomness used to compute the RLC
config.rlc_rlp = config.rlp.rlc_rlp(cb, r)
let mult_diff = config.mult_diff.expr();
(FixedTableTag::RMult, config.rlp.num_bytes(), mult_diff) in @FIXED
```

## IsEmptyTreeGadget

`IsEmptyTreeGadget` returns `1` when the trie is empty or when there is `0` at the modified position
in the branch (meaning there is no child at this position).

```
pub struct IsEmptyTreeGadget<F> {
    is_in_empty_trie: IsEqualGadget<F>,
    is_in_empty_branch: IsEqualGadget<F>,
}
```

We can use `IsEmptyTreeGadget` to check whether the (account / storage) leaf exists. Note that the gadget
is to be used only in the context of a leaf as it uses `parent_data.rlc` to execute the checks:

```
let is_in_empty_trie =
    IsEqualGadget::construct(&mut cb.base, parent_rlc.expr(), empty_root_rlc.expr());
let is_in_empty_branch =
    IsEqualGadget::construct(&mut cb.base, parent_rlc.expr(), 0.expr());
```

## DriftedGadget

`DriftedGadget` handles the leaf being moved from one branch to a newly created branch.

Sometimes `S` and `C` proofs are not of the same length. For example, when a new account `A1` is added,
the following scenario might happen. Let us say that the account that is being added has the address
(in nibbles):
``` 
[8, 15, 1, ...]
``` 

And let us say there already exists an account `A` with the following nibbles:
```
[8, 15, 3, ...]
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

So we have:
```
                              Branch0
Node_0_0 Node_0_1 ...              Node_0_8                 ... Node_0_15
                                      |
                        Node_1_0 Node_1_1 ... Node_1_15
                                                  |
                                                  A
```

Before we add the account `A1`, we first obtain the `S` proof which will contain the account `A` as a leaf
because the first part of the address `[8, 15]` is the same and when going down the trie retrieving
the elements of a proof, the algorithm arrives to the account `A`.

When we add the account `A1`, it cannot be placed at position 15 in `Branch1` because it is already
occupied by the account `A`. For this reason, a new branch `Branch2` is added.
Now, the third nibble of the accounts `A` and `A1` is considered. The account `A` drifts into a new branch
to position 3, while the account `A1` is placed at position 1 in `Branch2`.

Thus, the `C` proof has one element more than the `S` proof (the difference is due to `Branch2`).

```
S proof              || C proof
Branch0              || Branch0
Branch1              || Branch1
(Placeholder branch) || Branch2
A                    || A1
```

Note that the scenario is reversed (`S` and `C` are turned around) when a leaf is deleted
from the branch with exactly two leaves.

To preserve the parallel layout, the circuit uses a placeholder branch that occupies the columns
in `S` proof parallel to `Branch2`.

Having a parallel layout is beneficial for multiple reasons, for example having the layout as below
would cause problems with selectors such as `is_branch_child` as there would be account and branch
in the same row. Also, it would make the lookups more complicated as it is much easier to enable
a lookup if accounts `A` and `A1` are in the same row. Non-parallel layout:

```
S proof              || C proof
Branch0              || Branch0
Branch1              || Branch1
A                    || Branch2
                     || A1
```



```
pub struct DriftedGadget<F> {
    drifted_rlp_key: ListKeyGadget<F>,
}
```




## ListKeyGadget