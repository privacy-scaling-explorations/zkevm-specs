# Modified extension

```
pub(crate) struct ModExtensionGadget<F> {
    rlp_key: [ListKeyGadget<F>; 2],
    is_not_hashed: [LtGadget<F, 2>; 2],
    is_short_branch: IsZeroGadget<F>,
    is_key_part_odd: [Cell<F>; 2], // Whether the number of nibbles is odd or not.
    mult_key: Cell<F>,
}
```

ModExtensionGadget covers the cases when an extension node is replaced by another (shorter or longer) extension node.

For example, let's have the following branch `B`:
```
Child0 Child1 Child2 ... Child15
```

Let's say the path to this branch contains the following nibbles: `n1 n2 n3`.
Let's say that `Child2` is an extension node `E` with nibbles `n4 n5 n6 n7`.
That means we have a branch `B1` at path `n1 n2 n3 2 n4 n5 n6 n7`.
Note that the nibble `2` comes from the fact that `Child2` is
at position `2` in its parent branch.

Branch `B`:
```
Child0    Child1    Child2             ...            Child15
                  n4 n5 n6 n7
                   Branch B1
```

If we now insert a new leaf `L` at path `n1 n2 n3 2 n4 n5 m1`, the extension
node `E` with nibbles `n4 n5 n6 n7` will be replaced by an extension
node `E1` with nibbles `n4 n5`. This extension node will have a branch
`B0` with two nodes:
 * the newly inserted leaf `L` at position `m1`,
 * the newly created extension node `E2` at position `n6` with nibble `n7` and `B1` as its branch.
```
Child0    Child1    Child2             ...            Child15
                    n4 n5 (middle)
                   Branch B0 
                   m1     n6 (short)
                          n7
```

In the case above, the `S` proof returned by `get_Proof` contains the extension node `E` with nibbles `n1 n2 n3 2 n4 n5 n6 n7`.
The proof does not return its underlying branch, because the proof was asked for the path `n1 n2 n3 2 n4 n5 m1` (the newly inserted leaf `L`) which
did not exist before the leaf `L` has been added.
However, as the extension node witness data comes together with its underlying branch, the `S` proof witness actually does not contain the extension node `E`.
In fact, a placeholder branch and a placeholder leaf is added to
the `S` proof.
Instead, the witness data for `E` is added after the leaf and is named `long` extension node (see more about it below).

The `C` proof contains the leaf `L` as the last proof element, the branch `B0` as the element above it, and the extension `E1` (nibbles `n4 n5`) as the element above the branch `B0`. The extension node `E1` is named `middle` extension node.

The `C` proof also contains the extension node `E2` as the neighbour node of the leaf `L`.
However, only the hash of `E2` is stored as the neighbour node, there is no unhashed version of `E2` in the `C` proof.
For this reason, `E2` is added after the leaf and is named `short` extension node (more below).

## Witness

As mentioned above, additional witness data is added in the case of modified extension node after the leaf node.

For example, if we have an extension node `E` with nibbles `1 2 3 4 5 6` and
then a leaf `L` is added at the path `1 2 3 4 4`, a new extension node `E1` appears with nibbles `1 2 3 4`. The leaf `L` in in the underlying branch `B0` of `E1` at position `4`. At position `5` in `B0` we have the new extension node `E2` with one nibble `6`.

The witness for `E` (long extension node) contains the information about nibbles (the first row: `18 = 1 * 16 + 2, 54 = 3 * 16 + 4, 86 = 5 * 16 + 6`), about second nibbles (the second row: `2 4 6`), and the hash of the branch (the third row): 

```
[132 0 18 52 86 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
[0 0 2 4 6 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
[160 242 103 96 237 221 251 248 185 13 94 94 110 182 111 241 65 198 200 217 40 21 99 86 252 13 220 217 104 115 173 242 92 0]
```

The witness for `E2` (short extension node) contains the information about nibbles (the first row: `22 = 16 + 6`), about second nibbles (the second row, but there are no second nibbles in this case), and the hash of the branch (the third row): 

```
[22 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
[160 242 103 96 237 221 251 248 185 13 94 94 110 182 111 241 65 198 200 217 40 21 99 86 252 13 220 217 104 115 173 242 92 0]
```

## Constraints

It needs to be checked that the long extension node is in the parent branch (branch above placeholder branch)
in the `S` proof (or in `C` proof in case of deletion).
Also, it needs to be checked that the short extension node is in the branch of the newly
added (middle) extension node (in the special case of the short extension node being a branch the constraint looks a bit different):

```
ifx!{or::expr(&[parent_data[is_s.idx()].is_root.expr(), not!(is_not_hashed)]) => {
    // Hashed extension node in long extension is in parent branch
    require!((1.expr(), rlc.expr(), num_bytes.expr(), parent_data_lo[is_s.idx()].clone(), parent_data_hi[is_s.idx()].clone()) =>> @KECCAK);
} elsex {
    // Non-hashed extension node in parent branch
    require!(rlc => parent_data_rlc);
}} 
```

The nibbles of the long extension node needs to be the same as the concatenation of the nibbles of the middle extension node with the nibble denoting the position in the newly added branch and the nibbles of the short node:
```
require!(rlc_after_short => nibbles_rlc_long
```

There are two special cases:
 * the middle extension node is a branch,
 * the short extension node is a branch.

When the middle extension node is a branch the constraints do not change.

When the short extension node is a branch, the parent constraint is as follows:
```
if is_s {
    ifx!{or::expr(&[parent_data[is_s.idx()].is_root.expr(), not!(is_not_hashed)]) => {
        require!((1.expr(), rlc.expr(), num_bytes.expr(), parent_data_lo[is_s.idx()].clone(), parent_data_hi[is_s.idx()].clone()) =>> @KECCAK);
    } elsex {
        require!(rlc => parent_data_rlc);
    }}
} else {
    ifx!{or::expr(&[parent_data[is_s.idx()].is_root.expr(), not!(is_not_hashed)]) => {
        let branch_rlp_word = rlp_value[1].word();
        require!(branch_rlp_word.lo() => parent_data_lo[1]);
        require!(branch_rlp_word.hi() => parent_data_hi[1]);
    } elsex {
        require!(rlp_value[1].rlc_rlp() => parent_data_rlc);
    }}
}
```

And the concatenation of nibbles constraint is:
```
require!(middle_key_rlc => nibbles_rlc_long);
```

To distinguish between the normal case and the case when the short extension node is a branch, both long and short extension node witness 
are made the same in the case of the short extension node being a branch.
The gadget `IsZeroGadget` is then used to distinguish the cases.
```
config.is_short_branch = IsZeroGadget::construct(
    &mut cb.base,
    key_rlc[0].expr() - key_rlc[1].expr(),
);
```

