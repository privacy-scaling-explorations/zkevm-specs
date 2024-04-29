# Proof chain 

The selector `not_first_level` denotes whether the node is not in the first account trie level.
Thus, each account modification proof starts with `not_first_level = 0` rows.
However, a fixed column cannot be used because the first level can appear at different rows in different
proofs. Instead, an advice column is used, but it needs to be ensured that there cannot be any rogue
assignments.

Potential attacks:

 - `not_first_level` is assigned to 1 in the first level of the proof. This way the attacker could avoid
   checking that the hash of the first level node is the same as the trie root, which would make
   the proof meaningless. We prevent this by ensuring the first row has `not_first_level = 0`
   (for the first row we have a fixed column selector), that after the storage leaf (proof
   ends with a storage leaf or account leaf) there is a row with `not_first_level = 0`,
   and that after the account leaf when it is non storage modification there
   is a row with `not_first_level = 0`.
 - `not_first_level` is assigned to 0 in the middle of the proof - in this case the address RLC
   constraints fail.
 - Additional proof is added between the proofs (we have more `not_first_level = 0` than expected) -
   in this case the `start_root/final_root` lookups will fail.
 - Proof without account proof part (only having storage proof) - the attacker could omit the witness
   for account proof and thus avoid any account related checks. This is prevented with constraints
   that ensure there is always an account proof before the storage proof.

It needs to be ensured that `start_root` and `final_root` change only in the first row of
the `not_first_level = 0` node.

Note: Comparing the roots with the hash of branch / extension node in the first level
(or account leaf if in the first level) is done in `branch_hash_in_parent.rs`, `extension_node.rs`
(or `account_leaf_storage_codehash.rs` if the account leaf is in the first level).

### Proof chaining constraints

#### First row needs to have not_first_level = 0 (account leaf key)

In the first row, it needs to be `not_first_level = 0`. The selector `q_not_first`
is a fixed column, so can rely on it we are really in the first row.

Two nodes can appear in the first level: account leaf or branch / extension node.
The storage leaf cannot appear as it requires to have an account leaf above it
(a separate constraint for this).
Here, we check for the case when the account leaf is in the first level.

#### First row needs to have not_first_level = 0 (branch init)",

In the first row, it needs to be `not_first_level = 0`. The selector `q_not_first`
is a fixed column, so can rely on it we are really in the first row.

Two nodes can appear in the first level: account leaf or branch / extension node.
The storage leaf cannot appear as it requires to have an account leaf above it
(a separate constraint for this).
Here, we check for the case when the branch / extension node is in the first level.
  
#### not_first_level = 0 follows the last storage leaf row (account leaf)

When there is a last storage leaf row in the previous row, in the current row it needs
to be `not_first_level = 0` (we are in account leaf).
  
#### not_first_level = 0 follows the last storage leaf row (branch init)

When there is a last storage leaf row in the previous row, in the current row it needs
to be `not_first_level = 0` (we are in branch init).


#### not_first_level = 0 follows the last account leaf row when non storage mod proof (account leaf)

When there is a last account leaf row in the previous row and the proof is about
non storage modification (proof ends with account leaf),
in the current row it needs to be `not_first_level = 0` (we are in account leaf).

#### not_first_level = 0 follows the last account leaf row when non storage mod proof (branch init)
    
When there is a last account leaf row in the previous row and the proof is about
non storage modification (proof ends with account leaf),
in the current row it needs to be `not_first_level = 0` (we are in branch init).

#### not_first_level does not change except at is_branch_init or is_account_leaf_key_s or is_storage_leaf_key_s

`not_first_level` can change only in `is_branch_init` or `is_account_leaf_key_s` or
`is__leaf_key_s`.

Note that the change `not_first_level = 1` to `not_first_level = 0` (going to the first level)
is covered by the constraints above which constrain when such a change can occur.
On the other hand, this constraint ensured that `not_first_level` is changed in the middle
of the node rows.

#### start_root can change only when in the first row of the first level

`start_root` can change only in the first row of the first level.
We check that it stays the same always except when `not_first_level_prev = not_first_level_cur + 1`,

#### final_root can change only when in the first row of the first level

We check that it stays the same always except when `not_first_level_prev = not_first_level_cur + 1`,
that means when `not_first_level` goes from 1 to 0.

#### final_root_prev = start_root_cur when not_first_level = 1 -> not_first_level = 0

When we go from one modification to another, the previous `final_root` needs to be
the same as the current `start_root`.
    
#### not_first_level 0 -> 1 in branch init after the first level

If `not_first_level` is 0 in a previous row (being in branch init),
then `not_first_level` needs to be 1 in the current row (preventing two consecutive
blocks to be `not_first_level = 0`).

#### address_rlc is 0 in first row of first level

It needs to be ensured there is an account proof before the
storage proof. Otherwise the attacker could use only a storage proof with a properly
set `address_rlc` (storage mod lookup row contains `val_prev`, `val_cur`, `key_rlc`,
`address_rlc`) and it would not be detected that the account proof has not validated
(was not there).

We make sure `address_rlc = 0` at the beginning of the proof (except if it is
the account leaf which already have set the proper `address_rlc`). This makes sure
that there is a step where `address_rlc` is set to the proper value. This step
should happen in the account leaf first row (there is a separate constraint that
allows `address_rlc` to be changed only in the account leaf first row).
So to have the proper `address_rlc` we have to have an account leaf (and thus an account proof).

If the attacker would try to use a storage proof without an account proof, the first
storage proof node would need to be denoted by `not_first_level = 0` (otherwise
constraints related to `not_first_level` would fail - there needs to be `not_firstl_level = 0`
after the end of the previous proof). But then if this node is a branch, this constraint
would make sure that `address_rlc = 0`. As `address_rlc` cannot be changed later on
in the storage proof, the lookup will fail (except for the negligible probability that
the lookup really requires `address_rlc = 0`). If the first node is a storage leaf, we
need to ensure in a separate constraint that `address_rlc = 0` in this case too.

#### address_rlc is 0 in first row of first level when in storage leaf

Ensuring that the storage proof cannot be used without the account proof - in case the storage
proof would consist only of a storage leaf.

#### address_rlc does not change except at is_account_leaf_key_s or branch init in first level

It needs to be ensured that `address_rlc` changes only at the first row of the account leaf 
or in the branch init row if it is in the first level.
