# Start

`StartConfig` ensures the initial values in the [memory](main.md) lookup tables are set properly.
The memory mechanism is used for `MainData`, `ParentData`, and `KeyData`.

## MainData

For `MainData`, the `StartConfig` sets `proof_type`, `is_below_account`, `address_rlc`,
`root_prev`, and `root`.

The `proof_type` is set to one of the following:
 - NonceChanged = 1
 - BalanceChanged = 2
 - CodeHashExists = 3
 - AccountDestructed = 4
 - AccountDoesNotExist = 5
 - StorageChanged = 6
 - StorageDoesNotExist = 7

The `is_below_account` is set to `false` as the proof always start with an account proof.
This value is later updated to `true` in the account leaf before the rows of the storage proof
begin - `is_below_account` acts as a selector to trigger constraints that are needed in the
first level of the storage proof (for example, checking the storage trie root being in the 
account leaf).

The `address_rlc` is set to the account address RLC. This value is updated in the account leaf
to the storage key RLC.

The values `root_prev` and `root` are set to the previous and current root of the state trie.
These two values never change in the proof rows.

## ParentData

For `ParentData`, the `StartConfig` sets `rlc`, `is_root`, `is_placeholder`, and
`drifted_parent_rlc`.

The `rlc` is set to the root of the state trie. This value is used to check that the RLC
of the node below is `rlc`. In the start case, this means that the RLC of the top element
of the trie is `rlc`. In the branch case, this means that the RLC of the modified element
in the branch is `rlc`. In the account leaf case, this means that the RLC of the top element
of the storage trie is `rlc`.

The `is_root` is set to `true`. This value is set to `false` in all subsequent nodes.

The `is_placeholder` is set to `false`. This value is set to `true` in the branches
that appear only as a placeholder in one of the two parallel proofs - in some cases
one of the proofs has one branch less than the other (details in branch documentation).

The `drifted_parent_rlc` is set to the root of the state trie. This value is different from
the `rlc` only in the case of a placeholder branch.

## KeyData

For `KeyData`, the `StartConfig` sets `rlc`, `mult`, `num_nibbles`, `is_odd`,
`drifted_rlc`, `drifted_mult`, `drifted_num_nibbles`, and `drifted_is_odd`.