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

We need to include the account `A` that drifted into `Branch2` in the `C` proof too. This is because
we need to check that `Branch2` contains exactly two leaves: `A1` and `A` after it moved down from
`Branch1`. We need to also check that the account `A` in `S` proof (in `Branch1`) differs 
from the account `A` in `C` proof (in `Branch2`) in exactly one key nibble (this is different
if an extension node is added instead of a branch), everything else stays the same (the value
stored in the leaf).

An example of `getProof` output where `S` proof have two elements (branch and account leaf):

```
[248 241 160 255 151 217 75 103 5 122 115 224 137 233 146 50 189 95 178 178 247 44 237 22 101 231 39 198 40 14 249 60 251 151 15 128 128 128 128 160 60 79 85 51 115 192 158 157 93 223 211 100 62 94 72 146 251 82 116 111 190 139 246 12 252 146 211 122 66 110 206 20 128 160 120 190 160 200 253 109 255 226 49 189 87 112 136 160 23 77 119 59 173 185 188 145 251 156 155 144 100 217 100 114 109 106 128 160 69 72 113 186 79 146 63 86 46 218 1 200 131 76 71 142 217 35 30 209 101 239 91 47 163 221 136 130 249 155 236 112 160 49 65 26 94 193 156 227 78 42 198 56 211 105 254 0 33 31 96 41 208 40 13 215 156 51 173 132 112 34 192 121 49 160 244 154 252 18 232 96 245 36 84 15 253 182 157 226 247 165 106 144 166 1 2 140 228 170 110 87 112 80 140 149 162 43 128 160 20 103 6 95 163 140 21 238 207 84 226 60 134 0 183 217 11 213 185 123 139 201 37 22 227 234 220 30 160 20 244 115 128 128 128]
[248 102 157 55 236 125 29 155 142 209 241 75 145 144 143 254 65 81 209 56 13 192 157 236 195 213 73 132 11 251 149 241 184 70 248 68 1 128 160 112 158 181 221 162 20 124 79 184 25 162 13 167 162 146 25 237 242 59 120 184 154 118 137 92 181 187 152 115 82 223 48 160 7 190 1 231 231 32 111 227 30 206 233 26 215 93 173 166 90 214 186 67 58 230 71 161 185 51 4 105 247 198 103 124]
```

An example of `getProof` output where `C` proof have three elements (branch, added branch, and account leaf):

```
[248 241 160 188 253 144 87 144 251 204 78 148 203 12 141 0 77 176 70 67 92 90 100 110 40 255 28 218 97 116 184 26 121 18 49 128 128 128 128 160 60 79 85 51 115 192 158 157 93 223 211 100 62 94 72 146 251 82 116 111 190 139 246 12 252 146 211 122 66 110 206 20 128 160 120 190 160 200 253 109 255 226 49 189 87 112 136 160 23 77 119 59 173 185 188 145 251 156 155 144 100 217 100 114 109 106 128 160 69 72 113 186 79 146 63 86 46 218 1 200 131 76 71 142 217 35 30 209 101 239 91 47 163 221 136 130 249 155 236 112 160 49 65 26 94 193 156 227 78 42 198 56 211 105 254 0 33 31 96 41 208 40 13 215 156 51 173 132 112 34 192 121 49 160 244 154 252 18 232 96 245 36 84 15 253 182 157 226 247 165 106 144 166 1 2 140 228 170 110 87 112 80 140 149 162 43 128 160 20 103 6 95 163 140 21 238 207 84 226 60 134 0 183 217 11 213 185 123 139 201 37 22 227 234 220 30 160 20 244 115 128 128 128]
[248 81 128 128 128 128 128 128 128 160 222 45 71 217 199 68 20 55 244 206 68 197 49 191 78 208 106 209 111 87 254 9 221 230 148 86 131 219 7 121 62 140 160 190 214 56 80 83 126 135 17 104 48 181 30 249 223 80 59 155 70 206 67 24 6 82 98 81 246 212 143 253 181 15 180 128 128 128 128 128 128 128 128]
[248 102 157 32 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 184 70 248 68 1 23 160 112 158 181 221 162 20 124 79 184 25 162 13 167 162 146 25 237 242 59 120 184 154 118 137 92 181 187 152 115 82 223 48 160 7 190 1 231 231 32 111 227 30 206 233 26 215 93 173 166 90 214 186 67 58 230 71 161 185 51 4 105 247 198 103 124]
```

We can observe that there is a difference of one nibble in the key. In the first proof, the nibbles
are compressed as: `[55, 236, 125, ...]`. In the second proof, the nibbles are compressed as:
`[32, 133, 130, ...]`. The difference is that in the first row there is a first nibble `7 = 55 - 48`.
This nibble is not present in the account `A` when moved down into `Branch2` because `7` is the position
where the account `A` is placed in `Branch2`.

`DriftedGadget` contains a field `drifted_rlp_key`: `ListKeyGadget` which stores the key of the drifted
leaf.

```
pub struct DriftedGadget<F> {
    drifted_rlp_key: ListKeyGadget<F>,
}
```

The `DriftedGadget` constructor is given below:

```
pub(crate) fn construct(
    cb: &mut MPTConstraintBuilder<F>,
    parent_data: &[ParentData<F>],
    key_data: &[KeyData<F>],
    expected_key_rlc: &[Expression<F>],
    leaf_no_key_rlc: &[Expression<F>],
    drifted_item: &RLPItemView<F>,
    r: &Expression<F>,
)
```

### Constraints

The key RLC of the drifted leaf needs to be the same as the key RLC of the leaf before it drifted. The leaf
before the drift has more nibbles in the leaf key bytes, while these nibbles move to the path to the leaf for
the leaf after the drift:
```
key_rlc = expected_key_rlc
```

The total number of nibbles needs to be `64`. The value `key_num_nibbles` is obtained from `key_data` and
`num_nibbles` is the number of nibbles in the drifted leaf key:
```
key_num_nibbles + num_nibbles = 64
```

Complete the drifted leaf rlc by adding the bytes on the value row
The drifted leaf needs to be in the newly created branch (at `drifted_index`). The value `leaf_rlc` is
computed using the drifted leaf key and the value RLC (`leaf_no_key_rlc`):
```
((1, leaf_rlc, config.drifted_rlp_key.rlp_list.num_bytes(), parent_data[is_s.idx()].drifted_parent_rlc.expr()) in @KECCAK)
```

## WrongGadget

When `NonExistingAccountProof` or `NonExistingStorageProof`
proof type we can have two subtypes: with a wrong leaf and without a wrong leaf.
Without wrong leaf proof contains only branches and a placeholder leaf.
In this case, it is checked that there is nil in the parent branch
at the proper position. Note that we need an (placeholder) account
leaf for lookups and to know when to check that parent branch has a nil.

<!--
In `is_wrong_leaf is bool` we only check that `is_wrong_leaf` is a boolean values.
Other wrong leaf related constraints are in other gates.

`is_wrong_leaf` can be set to 1 only when the proof is not non_existing_account proof.
-->



## ListKeyGadget