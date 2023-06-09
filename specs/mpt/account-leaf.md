# Account leaf

An example account leaf RLP stream:
<!--
TestAccountAddPlaceholderExtension
-->
```
[248 108 157 52 45 53 199 120 18 165 14 109 22 4 141 198 233 128 219 44 247 218 241 231 2 206 125 246 58 246 15 3 184 76 248 74 4 134 85 156 208 108 8 0 160 86 232 31 23 27 204 85 166 255 131 69 230 146 192 248 110 91 72 224 27 153 108 173 192 1 98 47 181 227 99 180 33 160 197 210 70 1 134 247 35 60 146 126 125 178 220 199 3 192 229 0 182 83 202 130 39 59 123 250 216 4 93 133 164 112]
```

And after the balance is modified:
```
[248 101 156 58 168 111 115 58 191 32 139 53 139 168 184 7 8 29 109 70 164 7 116 82 56 174 242 193 51 253 77 184 70 248 68 4 23 160 86 232 31 23 27 204 85 166 255 131 69 230 146 192 248 110 91 72 224 27 153 108 173 192 1 98 47 181 227 99 180 33 160 197 210 70 1 134 247 35 60 146 126 125 178 220 199 3 192 229 0 182 83 202 130 39 59 123 250 216 4 93 133 164 112]
```

The account leaf `Node` in the circuit looks:
```
{
"address":[204,228,98,4,186,168,111,115,58,191,32,139,53,139,168,184,7,8,29,109,70,164,7,116,82,56,174,242,193,51,253,77],
"list_rlp_bytes":[[248,108],[248,101]],
"value_rlp_bytes":[[184,76],[184,70]],
"value_list_rlp_bytes":[[248,74],[248,68]],
"drifted_rlp_bytes":[248,107],
"wrong_rlp_bytes":[248,101]},
"storage":null,
"values":[
    [157,52,45,53,199,120,18,165,14,109,22,4,141,198,233,128,219,44,247,218,241,231,2,206,125,246,58,246,15,3,0,0,0,0],
    [156,58,168,111,115,58,191,32,139,53,139,168,184,7,8,29,109,70,164,7,116,82,56,174,242,193,51,253,77,0,0,0,0,0],[4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [134,85,156,208,108,8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0],
    [160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,112,0],
    [4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [23,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0],
    [160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,112,0],
    [156,61,53,199,120,18,165,14,109,22,4,141,198,233,128,219,44,247,218,241,231,2,206,125,246,58,246,15,3,0,0,0,0,0],
    [156,58,168,111,115,58,191,32,139,53,139,168,184,7,8,29,109,70,164,7,116,82,56,174,242,193,51,253,77,0,0,0,0,0]
],
"keccak_data":[
    [248,108,157,52,45,53,199,120,18,165,14,109,22,4,141,198,233,128,219,44,247,218,241,231,2,206,125,246,58,246,15,3,184,76,248,74,4,134,85,156,208,108,8,0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,112],[248,101,156,58,168,111,115,58,191,32,139,53,139,168,184,7,8,29,109,70,164,7,116,82,56,174,242,193,51,253,77,184,70,248,68,4,23,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,112],
    [248,107,156,61,53,199,120,18,165,14,109,22,4,141,198,233,128,219,44,247,218,241,231,2,206,125,246,58,246,15,3,184,76,248,74,4,134,85,156,208,108,8,0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,112]
]
}
```

The rows of `values` are:
```
AccountKeyS
AccountKeyC
AccountNonceS
AccountBalanceS
AccountStorageS
AccountCodehashS
AccountNonceC
AccountBalanceC
AccountStorageC
AccountCodehashC
AccountDrifted
AccountWrong	
```

## Old

An account leaf occupies 8 rows.
Contrary as in the branch rows, the `S` and `C` leaves are not positioned parallel to each
other. The rows are as follows:

```
ACCOUNT_LEAF_KEY_S
ACCOUNT_LEAF_KEY_C
ACCOUNT_NON_EXISTING
ACCOUNT_LEAF_NONCE_BALANCE_S
ACCOUNT_LEAF_NONCE_BALANCE_C
ACCOUNT_LEAF_STORAGE_CODEHASH_S
ACCOUNT_LEAF_STORAGE_CODEHASH_C
ACCOUNT_DRIFTED_LEAF
```

Example:
```
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[0,0,0,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[184,70,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[184,70,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]

[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]

[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

Lookups:
We have nonce and balance in the same row - to enable lookups into the same columns (`value_prev`, `value`),
we enable nonce lookup in `ACCOUNT_LEAF_NONCE_BALANCE_S` row and balance lookup in `ACCOUNT_LEAF_NONCE_BALANCE_C` row.
This means we copy nonce C RLC to `ACCOUNT_LEAF_NONCE_BALANCE_S` row,
and balance S RLC to `ACCOUNT_LEAF_NONCE_BALANCE_C` row.
Constraints are added to ensure everything is properly copied.
```

There are two main scenarios when an account is added to the trie:
 1. There exists another account which has the same address to the some point as the one that
 is being added, including the position of this account in the branch.
 In this case a new branch is added to the trie.
 The existing account drifts down one level to the new branch. The newly
 added account will also appear in this branch. For example, let us say that we have the account `A`
 with nibbles `[3, 12, 3]` in the trie. We then add the account `A1` with nibbles `[3, 12, 5]`
 to the trie. The branch will appear (at position `[3, 12]`) which will have `A` at position 3
 and `A1` at position 5. This means there will be an additional branch in `C` proof (or in `S`
 proof when the situation is reversed - we are deleting the leaf instead of adding) and
 for this reason we add a placeholder branch for `S` proof (for `C` proof in reversed situation)
 to preserve the circuit layout (more details about this technicality are given below).

 2. The branch where the new account is to be added has nil node at the position where the new account
 is to be added. For example, let us have a branch at `[3, 12]`, we are adding a leaf with the
 first three nibbles as `[3, 12, 5]`, and the position 5 in our branch is not occupied.
 There does not exist an account which has the same address to the some point.
 In this case, the `getProof` response does not end with a leaf, but with a branch.
 To preserve the layout, a placeholder account leaf is added.

In what follows we present the constraints for the account leaf. These are grouped into five
files:
 * `account_leaf_key.rs`
 * `account_leaf_nonce_balance.rs`
 * `account_leaf_storage_codehash.rs`
 * `account_leaf_key_in_added_branch.rs`
 * `account_non_existing.rs`

In the last section, we give an example of the nonce modification proof.

## Account key constraints

### Account leaf RLC after key

#### Account leaf key s_main.rlp1 = 248

Account leaf always starts with 248 because its length is always longer than 55 bytes due to
containing two hashes - storage root and codehash, which are both of 32 bytes. 
248 is RLP byte which means there is `1 = 248 - 247` byte specifying the length of the remaining
list. For example, in `[248,112,157,59,...]`, there are 112 byte after the second byte.

#### Leaf key RLC

In each row of the account leaf we compute an intermediate RLC of the whole leaf.
The RLC after account leaf key row is stored in `acc` column. We check the stored value
is computed correctly.

### Zeros in s_main.bytes & c_main.rlp1 & c_main.rlp2 after key ends

Key RLC is computed over all of `s_main.bytes[1], ..., s_main.bytes[31], c_main.rlp1, c_main.rlp2`
because we do not know the key length in advance.
To prevent changing the key and setting `s_main.bytes[i]` (or `c_main.rlp1/c_main.rlp2`) for
`i > key_len + 1` to get the desired key RLC, we need to ensure that
`s_main.bytes[i] = 0` for `i > key_len + 1`.

Note: the key length is always in `s_main.bytes[0]` here as opposed to storage
key leaf where it can appear in `s_rlp2` too. This is because the account
leaf contains nonce, balance, ... which makes it always longer than 55 bytes,
which makes a RLP to start with 248 (`s_rlp1`) and having one byte (in `s_rlp2`)
for the length of the remaining stream.

### mult_diff

When the account intermediate RLC is computed in the next row (nonce balance row), we need
to know the intermediate RLC and the randomness multiplier (`r` to some power) from the current row.
The power of randomness `r` is determined by the key length - the intermediate RLC in the current row
is computed as (key starts in `s_main.bytes[1]`):

```
rlc = s_main.rlp1 + s_main.rlp2 * r + s_main.bytes[0] * r^2 + key_bytes[0] * r^3 + ... + key_bytes[key_len-1] * r^{key_len + 2}
```

So the multiplier to be used in the next row is `r^{key_len + 2}`. 

`mult_diff` needs to correspond to the key length + 2 RLP bytes + 1 byte for byte that contains the key length.
That means `mult_diff` needs to be `r^{key_len+1}` where `key_len = s_main.bytes[0] - 128`.

### Account leaf address RLC & nibbles count (branch not placeholder)

#### Account leaf key with even nibbles: s_main.bytes[1] = 32

If there is an even number of nibbles in the leaf, `s_main.bytes[1]` need to be 32.

#### Address RLC

Account leaf contains the remaining nibbles of the account address. Combining the path 
of the leaf in the trie and these remaining nibbles needs to be the same as the account
address which is given in the `address_rlc` column that is to be used by a lookup (see the
constraint below).

Address RLC needs to be computed properly - we need to take into account the path of the leaf 
in the trie and the remaining nibbles in the account leaf.

The intermediate RLC is retrieved from the last branch above the account leaf - this
presents the RLC after the path to the leaf is considered. After this, the bytes (nibbles
in a compacted form) in the leaf have to be added to the RLC.

#### Computed account address RLC same as value in address_rlc column

The computed key RLC needs to be the same as the value in `address_rlc` column.
This seems to be redundant (we could write one constraint instead of two:
`key_rlc_acc - address_rlc = 0`), but note that `key_rlc` is used in
`account_leaf_key_in_added_branch` and in cases when there is a placeholder branch
we have `key_rlc - address_rlc != 0` because `key_rlc` is computed for the branch
that is parallel to the placeholder branch.

Note that there is a similar constraint for the cases when the account leaf is in the first level, but
here we do not fetch for the intermediate RLC from the branch above as there is no branch above.

#### Total number of address nibbles

Total number of account address nibbles nees to be 64. This is to prevent having short addresses
which could lead to a root node which would be shorter than 32 bytes and thus not hashed. That
means the trie could be manipulated to reach a desired root.

### Account leaf address RLC & nibbles count (after placeholder)

This gate is again similar to the gate `Account leaf address RLC & nibbles count (leaf not in first level, branch not placeholder)`, but with a leaf being after a branch placeholder.

#### Account address RLC after branch placeholder

The example layout for a branch placeholder looks like (placeholder could be in `C` proof too):
```
Branch 1S               || Branch 1C
Branch 2S (placeholder) || Branch 2C
Leaf S
Leaf C
```

Using `Previous key RLC` constraint we ensured that we copied the key RLC from Branch 1S
to Leaf S `accs.acc_c.rlc` column. So when add nibbles to compute the key RLC (address RLC)
of the account, we start with `accs.acc_c.rlc` value from the current row.

Although `key_rlc` is not compared to `address_rlc` in the case when the leaf
is below the placeholder branch (`address_rlc` is compared to the parallel leaf `key_rlc`), 
we still need properly computed `key_rlc` to reuse it in `account_leaf_key_in_added_branch`.

Note: `key_rlc - address_rlc != 0` when placeholder branch.

### Account delete

#### If account delete, there is either a placeholder leaf or a placeholder branch

We need to make sure there is no leaf when account is deleted. Two possible cases:
1. Account leaf is deleted and there is a nil object in branch. In this case we have 
    a placeholder leaf.
2. Account leaf is deleted from a branch with two leaves, the remaining leaf moves one level up
    and replaces the branch. In this case we have a branch placeholder.

So we need to check there is a placeholder branch when we have the second case.

Note: we do not need to cover the case when the (only) branch dissapears and only one
leaf remains in the trie because there will always be at least two leaves
(the genesis account) when account will be deleted,
so there will always be a branch / extension node (and thus placeholder branch).

### Range lookups

Range lookups ensure that `s_main`, `c_main.rlp1`, `c_main.rlp2` columns are all bytes (between 0 - 255).
Note that `c_main.bytes` columns are not used.

## Account leaf nonce balance constraints

An example rows of the account leaf are:

```
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[0,0,0,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[184,70,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[184,70,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]

[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]

[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```

In `ACCOUNT_LEAF_NONCE_BALANCE_S` row (fourth row), there is `S` nonce stored in `s_main`
and `S` balance in `c_main`. We can see nonce in `S` proof is `0 = 128 - 128`.

In `ACCOUNT_LEAF_NONCE_BALANCE_C` row (fifth row), there is `C` nonce stored in `s_main`
and `C` balance in `c_main`. We can see nonce in `C` proof is `1`.

The constraints for the first gate of `AccountLeafNonceBalanceChip` which is named
`Account leaf nonce balance RLC & RLP` are given below.

### Account leaf nonce balance RLC & RLP

#### Bool check is_nonce_long & Bool check is_balance_long

If nonce (same holds for balance) is smaller or equal to 128, then it will occupy only one byte:
`s_main.bytes[0]` (`c_main.bytes[0]` for balance).
We can see such case in the example above. The nonce there is 128 (meaning 0) before modification
and 1 (meaning 1) after modification.

In case nonce (same for balance) is bigger than 128, it will occupy more than 1 byte.
The example row below shows nonce value 142, while 129 means there is a nonce of byte
length `1 = 129 - 128`.
Balance in the example row below is: `28 + 5 * 256 + 107 * 256^2 + ... + 59 * 256^6`, while
135 means there are `7 = 135 - 128` bytes.
```
[rlp1 rlp2 bytes[0] bytes[1]]           rlp1 rlp2 bytes[0] bytes[1]   ...    ]
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
```

The `sel1` column in the `ACCOUNT_LEAF_KEY_S` or `ACCOUNT_LEAF_KEY_C` row
is used to mark whether nonce is of 1 byte (short) or more than 1 byte (long).
`sel1 = 1` means long, `sel1 = 0` means short.
`Bool check is_nonce_long` constraint ensures the value is boolean.

Analogously, `sel2` holds the information whether balance is long or short.
Bool check `is_balance_long` constraint ensures the `sel2` value is boolean.

#### s_main.bytes[i] = 0 for i > 0 when is_nonce_short

It is important that there are 0s in `s_main.bytes` after the nonce bytes end.
When nonce is short (1 byte), like in `[184,70,1,0,...]`, the constraint is simple:
`s_main.bytes[i] = 0` for all `i > 0`.

When nonce is long, the constraints need to be written differently because we do not
know the length of nonce in advance.
The row below holds nonce length specification in `s_main.bytes[0]`.
The length in the example below is `1 = 129 - 128`,
so the constraint needs to be `s_main.bytes[i] = 0` for
all `i > 1` (note that the actual value is in `s_main.bytes[1]`).

```
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
```

But instead of 129 we could have 130 or some other value in `s_main.bytes[0]`. For this
reason, the constraints are implemented using `key_len_lookup`, more about this approach
in what follows.

#### c_main.bytes[i] = 0 for i > 0 when is_balance_short

The balance constraints are analogous to the nonce constraints described above.
The difference is that balance is stored in `c_main.bytes`.

#### is_wrong_leaf is bool

When `non_existing_account_proof` proof type (which can be of two subtypes: with wrong leaf
and without wrong leaf, more about it below), the `is_wrong_leaf` flag specifies whether
the subtype is with wrong leaf or not.
When `non_existing_account_proof` without wrong leaf
the proof contains only branches and a placeholder account leaf.
In this case, it is checked that there is nil in the parent branch
at the proper position (see `account_non_existing`). Note that we need (placeholder) account
leaf for lookups and to know when to check that parent branch has a nil.

In `is_wrong_leaf is bool` we only check that `is_wrong_leaf` is a boolean values.
Other wrong leaf related constraints are in other gates.

#### is_wrong_leaf needs to be 0 when not in non_existing_account proof

`is_wrong_leaf` can be set to 1 only when the proof is not non_existing_account proof.

#### Nonce RLC long 

Besides having nonce (its bytes) stored in `s_main.bytes`, we also have the RLC
of nonce bytes stored in `s_mod_node_hash_rlc` column. The value in this column
is to be used by lookups.
`Nonce RLP long` constraint ensures the RLC of a nonce is computed properly when
nonce is long.

#### Nonce RLC short

Similarly as in `Nonce RLP long` constraint, 
`Nonce RLP short` constraint ensures the RLC of a nonce is computed properly when
nonce is short.

#### Balance RLC long 

Besides having balance (its bytes) stored in `c_main.bytes`, we also have the RLC
of nonce bytes stored in `c_mod_node_hash_rlc` column. The value in this column
is to be used by lookups.
`Balance RLP long` constraint ensures the RLC of a balance is computed properly when
balance is long.

#### Balance RLC short

Similarly as in `Balance RLP long` constraint, 
`Balance RLP short` constraint ensures the RLC of a balance is computed properly when
balance is short.

#### S nonce RLC is correctly copied to value_prev column

To enable lookup for nonce modification we need to have S nonce and C nonce in the same row.
For this reason, S nonce RLC is copied to `value_prev` column.

#### C nonce RLC is correctly copied to lookup row

To enable lookup for nonce modification we need to have S nonce and C nonce in the same row.
For this reason, C nonce RLC is copied to `value` column in `ACCOUNT_LEAF_NONCE_BALANCE_S` row.

#### C nonce RLC is correctly copied to NON_EXISTING_ACCOUNT row

To enable lookup for nonce modification we need to have S nonce and C nonce in the same row.
For this reason, C nonce RLC is copied to `value` column in `NON_EXISTING_ACCOUNT` row.

#### S balance RLC is correctly copied to C row

To enable lookup for balance modification we need to have S balance and C balance in the same row.
For this reason, S balance RLC is copied to `value_prev` column in C row.

#### S balance RLC is correctly copied to C row

To enable lookup for balance modification we need to have `S` balance and `C` balance
in the same row. For this reason, `S` balance RLC is copied to `sel2` column in `C` row.
This constraint checks whether the value is properly copied.

#### C balance RLC is correctly copied to value column

To enable lookup for balance modification we need to have S balance and C balance in the same row.
For this reason, C balance RLC is copied to `value` column in C row.
constraints.push((


#### If storage or balance or codehash modification: S nonce = C nonce

We need to ensure there is only one modification at a time. If there is storage or
balance or codehash modification, we need to ensure `S` nonce and `C` nonce are the same.

Note: For `is_non_existing_account_proof` we do not need this constraint,
`S` and `C` proofs are the same and we need to do a lookup into only one
(the other one could really be whatever).

#### If storage or nonce or codehash modification: S balance = C balance

We need to ensure there is only one modification at a time. If there is storage or
nonce modification, we need to ensure `S` balance and `C` balance are the same.

Note: For `is_non_existing_account_proof` we do not need this constraint,
`S` and `C` proofs are the same and we need to do a lookup into only one
(the other one could really be whatever).

#### Leaf nonce balance RLC

Computed RLC after nonce balance row is the same as the stored RLC value.

#### Leaf nonce RLC mult (nonce long)

When adding nonce bytes to the account leaf RLC we do:

```
rlc_after_nonce = rlc_tmp + s_main.bytes[0] * mult_tmp + s_main.bytes[1] * mult_tmp * r + ... + s_main.bytes[k] * mult_tmp * r^k
```

Note that `rlc_tmp` means the RLC after the previous row, while `mult_tmp` means the multiplier
(power of randomness `r`) that needs to be used for the first byte in the current row.

In this case we assumed there are `k + 1` nonce bytes. After this we continue adding bytes:
`rlc_after_nonce + b1 * mult_tmp * r^{k+1} + b2 * mult_tmp * r^{k+1} * r + ...
Note that `b1` and `b2` are the first two bytes that need to used next (balance bytes).

The problem is `k` can be different from case to case. For this reason, we store `r^{k+1}` in
`mult_diff_nonce` (which is actually `acc_c`).
That means we can compute the expression above as:
`rlc_after_nonce + b1 * mult_tmp * mult_diff_nonce + b2 * mult_tmp * mult_diff_nonce * r + ...

However, we need to ensure that `mult_diff_nonce` corresponds to `s_main.bytes[0]` where the length
of the nonce is specified. This is done using `key_len_lookup` below.

There is one more detail: when computing RLC after nonce, we compute also the bytes that come before
nonce bytes in the row. These are: `s_main.rlp1`, `s_main.rlp2`, `c_main.rlp1`, `c_main.rlp2`.
It is a bit confusing (we are limited with layout), but `c_main.rlp1` and `c_main.rlp2`
are bytes that actually appear in the account leaf RLP stream before `s_main.bytes`.
So we have:

```
rlc_after_nonce = rlc_tmp + s_main.rlp1 * mult_tmp + s_main.rlp2 * mult_tmp * r + c_main.rlp1 * mult_tmp * r^2 + c_main.rlp2 * mult_tmp * r^3 + s_main.bytes[0] * mult_tmp * r^4 + ... + s_main.bytes[k] * mult_tmp * r^4 * r^k
```

That means `mult_diff_nonce` needs to store `r^4 * r^{k+1}` and we continue computing the RLC
as mentioned above:

```
rlc_after_nonce + b1 * mult_tmp * mult_diff_nonce + b2 * mult_tmp * mult_diff_nonce * r + ...
```

Let us observe the following example.
```
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
```

Here:

```
rlc_after_nonce = rlc_tmp + 184 * mult_tmp + 78 * mult_tmp * r + 248 * mult_tmp * r^2 + 76 * mult_tmp * r^3 + 129 * mult_tmp * r^4 + 142 * mult_tmp * r^5
```

And we continue computing the RLC:

```
rlc_after_nonce + 135 * mult_tmp * mult_diff_nonce + 28 + mult_tmp * mult_diff_nonce * r + ...
```

#### Leaf nonce RLC mult (nonce short)

When nonce is short (occupying only one byte), we know in advance that `mult_diff_nonce = r^5`
as there are `s_main.rlp1`, `s_main.rlp2`, `c_main.rlp1`, `c_main.rlp2`, and `s_main.bytes[0]` bytes to be taken into account.

#### Leaf balance RLC mult (balance long)

We need to prepare the multiplier that will be needed in the next row: `acc_mult_final`.
We have the multiplier after nonce bytes were added to the RLC: `acc_mult_after_nonce`.
Now, `acc_mult_final` depends on the number of balance bytes. 

```
rlc_after_balance = rlc_after_nonce + b1 * acc_mult_after_nonce + ... + bl * acc_mult_after_nonce * r^{l-1}
```

Where `b1,...,bl` are `l` balance bytes. As with nonce, we do not know the length of balance bytes
in advance. For this reason, we store `r^l` in `mult_diff_balance` and check whether:

```
acc_mult_final = acc_mult_after_nonce * mult_diff_balance
```

Note that `mult_diff_balance` is not the last multiplier in this row, but the first in
the next row (this is why there is `r^l` instead of `r^{l-1}`).

#### Leaf balance RLC mult (balance short)

When balance is short, there is only one balance byte and we know in advance that the
multiplier changes only by factor `r`.

#### Leaf nonce balance s_main.rlp1 = 184

`s_main.rlp1` needs always be 184. This is RLP byte meaning that behind this byte
there is a string of length more than 55 bytes and that only `1 = 184 - 183` byte is reserved
for length (`s_main.rlp2`). The string is always of length greater than 55 because there
are codehash (32 bytes) and storage root (32 bytes) in the next row as part of this string.

The only exception is when `is_non_existing_account_proof = 1` & `is_wrong_leaf = 0`.
In this case the value does not matter as the account leaf is only a placeholder and
does not use `s_main.rlp1` and `s_main.rlp2`. Note that it uses `s_main` for nibbles
because the account address is computed using nibbles and this account address needs
to be as required by a lookup.

#### Leaf nonce balance c_main.rlp1 = 248

`c_main.rlp1` needs to always be 248. This is RLP byte meaning that behind this byte
there is a list which has one byte that specifies the length - `at c_main.rlp2`.

The only exception is when `is_non_existing_account_proof = 1` & `is_wrong_leaf = 0`.
In this case the value does not matter as the account leaf is only a placeholder and
does not use `c_main`. Note that it uses `s_main` for nibbles because the account address
is computed using nibbles and this account address needs to be as required by a lookup.
That means there is an account leaf which is just a placeholder but it still has the
correct address.

Example:
```
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
```
248 at c_main.rlp1 means one byte for length. This byte is 76, meaning there are 76 bytes after it.

#### Leaf nonce balance s_main.rlp2 - c_main.rlp2

`c_main.rlp2` specifies the length of the remaining RLP string. Note that the string
is `s_main.rlp1`, `s_main.rlp2`, `c_main.rlp1`, `c_main.rlp2`, nonce bytes, balance bytes.
Thus, `c_main.rlp2 = #(nonce bytes) + #(balance bytes) + 32 + 32`.
`s_main.rlp2` - `c_main.rlp2` = 2 because of two bytes difference: `c_main.rlp1` and c_main.rlp2`.

Example:
```
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
```
We can see: `78 - 76 - 1 - 1 = 0`.

#### Lean nonce balance c_main.rlp2

`c_main.rlp2 = #(nonce bytes) + #(balance bytes) + 32 + 32`.
Note that `32 + 32` means the number of codehash bytes + the number of storage root bytes.

#### Account leaf RLP length 

The whole RLP length of the account leaf is specified in the account leaf key row with
`s_main.rlp1 = 248` and `s_main.rlp2`. `s_main.rlp2` in key row actually specifies the length.
`s_main.rlp2` in nonce balance row specifies the length of the remaining string in nonce balance
row, so we need to check that `s_main.rlp2` corresponds to the key length (in key row) and
`s_main.rlp2` in nonce balance row. However, we need to take into account also the bytes
where the lengths are stored:

```
s_main.rlp2 (key row) - key_len - 1 (because key_len is stored in 1 byte) - s_main.rlp2 (nonce balance row) - 1 (because of s_main.rlp1) - 1 (because of s_main.rlp2) = 0
```

Example:
```
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
[184,70,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```
We can see: `106 - 33 - 1 - 70 - 1 - 1 = 0`.

### mult_diff_nonce

`mult_diff_nonce` needs to correspond to nonce length + 5 bytes:
`s_main.rlp1,` `s_main.rlp2`, `c_main.rlp1`, `c_main.rlp1`, 1 for byte with nonce length (`s_main.bytes[0]`).
That means `mult_diff_nonce` needs to be `r^{nonce_len+5}` where `nonce_len = s_main.bytes[0] - 128`.

Note that when nonce is short, `mult_diff_nonce` is not used (see the constraint above).

### 0s after nonce ends

Nonce RLC is computed over `s_main.bytes[1]`, ..., `s_main.bytes[31]` because we do not know
the nonce length in advance. To prevent changing the nonce and setting `s_main.bytes[i]` for
`i > nonce_len + 1` to get the correct nonce RLC, we need to ensure that
`s_main.bytes[i] = 0` for `i > nonce_len + 1`.

### mult_diff_balance

`mult_diff_balance` needs to correspond to balance length + 1 byte for byte that contains balance length.
That means `mult_diff_balance` needs to be `r^{balance_len+1}` where `balance_len = c_main.bytes[0] - 128`.

Note that when balance is short, `mult_diff_balance` is not used (see the constraint above).

### 0s after balance ends

Balance RLC is computed over `c_main.bytes[1]`, ..., `c_main.bytes[31]` because we do not know
the balance length in advance. To prevent changing the balance and setting `c_main.bytes[i]` for
`i > balance_len + 1` to get the correct balance RLC, we need to ensure that
`c_main.bytes[i] = 0` for `i > balance_len + 1`.

### Range lookups

Range lookups ensure that `s_main` and `c_main` columns are all bytes (0 - 255).

## Account leaf storage codehash constraints

The constraints in `account_leaf_storage_codehash.rs` apply to ACCOUNT_LEAF_STORAGE_CODEHASH_S and
ACCOUNT_LEAF_STORAGE_CODEHASH_C rows.

For example, the two rows might be:
```
[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]
[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]
```

Here, in `ACCOUNT_LEAF_STORAGE_CODEHASH_S` example row, there is `S` storage root stored in `s_main.bytes`
and `S` codehash in `c_main.bytes`. Both these values are hash outputs.
We can see `s_main.rlp2 = 160` which specifies that the length of the following string is `32 = 160 - 128`
(which is hash output). Similarly, `c_main.rlp2 = 160`.

In `ACCOUNT_LEAF_STORAGE_CODEHASH_C` example row, there is `C` storage root stored in `s_main.bytes`
and `C` codehash in `c_main.bytes`. Both these values are hash outputs.

### Account leaf storage codehash

#### Account leaf storage codehash s_main.rlp2 = 160

`s_main.rlp2` stores the RLP length of the hash of storage root. The hash output length is 32
and thus `s_main.rlp2` needs to be `160 = 128 + 32`. 

#### Account leaf storage codehash c_main.rlp2 = 160

`c_main.rlp2` stores the RLP length of the codehash. The hash output length is 32
and thus `c_main.rlp2` needs to be `160 = 128 + 32`. 

#### Storage root RLC 

`s_main.bytes` contain storage root hash, but to simplify lookups we need to have
the RLC of storage root hash stored in some column too. The RLC is stored in
`s_mod_node_hash_rlc`. We need to ensure that this value corresponds to the RLC
of `s_main.bytes`.

#### Codehash RLC

`c_main.bytes` contain codehash, but to simplify lookups we need to have
the RLC of the codehash stored in some column too. The RLC is stored in
`c_mod_node_hash_rlc`. We need to ensure that this value corresponds to the RLC
of `c_main.bytes`.

#### S codehash RLC is correctly copied to C row

To enable lookup for codehash modification we need to have S codehash
and C codehash in the same row.
For this reason, S codehash RLC is copied to `value_prev` column in C row.

##### C codehash RLC is correctly copied to value row

To enable lookup for codehash modification we need to have S codehash
and C codehash in the same row (`value_prev`, `value` columns).
C codehash RLC is copied to `value` column in C row.

#### If nonce or balance or codehash modification: storage_root_s = storage_root_c

If the modification is nonce or balance or codehash modification, the storage root needs to 
stay the same.

Note: For `is_non_existing_account_proof` we do not need this constraint,
`S` and `C` proofs are the same and we need to do a lookup into only one
(the other one could really be whatever).

#### If nonce or balance or storage modification: codehash_s = codehash_c

If the modification is nonce or balance or storage modification (that means
always except for `is_account_delete_mod` and `is_non_existing_account_proof`),
the storage root needs to stay the same.

Note: For `is_non_existing_account_proof` we do not need this constraint,
`S` and `C` proofs are the same and we need to do a lookup into only one
(the other one could really be whatever).

#### Account leaf storage codehash RLC

The RLC of the account leaf needs to be properly computed. We take the intermediate RLC
computed in the `ACCOUNT_LEAF_NONCE_BALANCE_*` row and add the bytes from the current row.
The computed RLC needs to be the same as the stored value in `acc_s` row.

### Account first level leaf without branch - compared to state root

Check hash of an account leaf to be state root when the leaf is without a branch (the leaf
is in the first level).

Note: the constraints for the first level branch to be compared to the state root
are in `branch_hash_in_parent`.

### Hash of an account leaf in a branch

Hash of an account leaf needs to appear (when not in first level) at the proper position in the
parent branch.

Note: the placeholder leaf appears when a new account is created (in this case there was
no leaf before and we add a placeholder). There are no constraints for
a placeholder leaf, it is added only to maintain the parallel layout.

### Hash of an account leaf when branch placeholder

When there is a placeholder branch above the account leaf (it means the account leaf
drifted into newly added branch, this branch did not exist in `S` proof), the hash of the leaf
needs to be checked to be at the proper position in the branch above the placeholder branch.

Note: a placeholder leaf cannot appear when there is a branch placeholder
(a placeholder leaf appears when there is no leaf at certain position, while branch placeholder
appears when there is a leaf and it drifts down into a newly added branch).

### Hash of an account leaf compared to root when branch placeholder in the first level

When there is a placeholder branch above the account leaf (it means the account leaf
drifted into newly added branch, this branch did not exist in `s` proof) in the first level,
the hash of the leaf needs to be checked to be the state root.

### Range lookups

Range lookups ensure that `s_main` and `c_main` columns are all bytes (between 0 - 255).

Note: `s_main.rlp1` and `c_main.rlp1` are not used.

## Account leaf in added branch (drifted leaf) constraints

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

The account leaf is distributed over 8 rows as described above:

```
ACCOUNT_LEAF_KEY_S
ACCOUNT_LEAF_KEY_C
ACCOUNT_NON_EXISTING
ACCOUNT_LEAF_NONCE_BALANCE_S
ACCOUNT_LEAF_NONCE_BALANCE_C
ACCOUNT_LEAF_STORAGE_CODEHASH_S
ACCOUNT_LEAF_STORAGE_CODEHASH_C
ACCOUNT_DRIFTED_LEAF
```

`ACCOUNT_DRIFTED_LEAF` row is where the account `A` (when in `Branch2`) is stored.
We can see the example below - the key of the account `A` (when in `Branch2`) is in the last
row. Note that key of the account `A` when in `Branch1` is in the first row.

```
[248 102 157 55 236 125 29 155 142 209 241 75 145 144 143 254 65 81 209 56 13 192 157 236 195 213 73 132 11 251 149 241 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 6]
[248 102 157 32 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 4]
[0 0 0 32 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 18]
[184 70 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 248 68 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 7]
[184 70 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 248 68 23 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 8]
[0 160 112 158 181 221 162 20 124 79 184 25 162 13 167 162 146 25 237 242 59 120 184 154 118 137 92 181 187 152 115 82 223 48 0 160 7 190 1 231 231 32 111 227 30 206 233 26 215 93 173 166 90 214 186 67 58 230 71 161 185 51 4 105 247 198 103 124 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 9]
[0 160 112 158 181 221 162 20 124 79 184 25 162 13 167 162 146 25 237 242 59 120 184 154 118 137 92 181 187 152 115 82 223 48 0 160 7 190 1 231 231 32 111 227 30 206 233 26 215 93 173 166 90 214 186 67 58 230 71 161 185 51 4 105 247 198 103 124 0 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 11]
[248 102 157 32 236 125 29 155 142 209 241 75 145 144 143 254 65 81 209 56 13 192 157 236 195 213 73 132 11 251 149 241 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 6 92 69 153 141 251 249 206 112 188 187 128 87 78 215 166 34 146 45 44 119 94 10 35 49 254 90 139 141 204 153 244 144 242 246 191 23 44 167 166 154 14 14 27 198 200 66 149 155 102 162 36 92 147 76 227 228 141 122 139 186 245 89 5 41 252 237 52 8 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 10]
```

We can observe that there is a difference of one nibble in the key. In the first row, the nibbles
are compressed as: `[55, 236, 125, ...]`. In the last row, the nibbles are compressed as:
`[32, 236, 125, ...]`. The difference is that in the first row there is a first nibble `7 = 55 - 48`.
This nibble is not present in the account `A` when moved down into `Branch2` because 7 is the position
where the account `A` is placed in `Branch2`.

### Account drifted leaf: intermediate leaf RLC after key"

#### Account leaf key s_rlp1 = 248

`s_rlp1` is always 248 because the account leaf is always longer than 55 bytes.

#### Account leaf key intermediate RLC

We check that the leaf RLC is properly computed. RLC is then taken and
nonce/balance & storage root / codehash values are added to the RLC (note that nonce/balance
& storage root / codehash are not stored for the drifted leaf because these values stay
the same as in the leaf before drift).
Finally, the lookup is used to check the hash that corresponds to this RLC is
in the parent branch at `drifted_pos` position.

### mult_diff

Similarly as in `account_leaf_key.rs`.
When the full account intermediate RLC is computed, we need
to know the intermediate RLC and the randomness multiplier (`r` to some power) from the key row.
The power of randomness `r` is determined by the key length - the intermediate RLC in the current row
is computed as (key starts in `s_main.bytes[1]`):

```
rlc = s_main.rlp1 + s_main.rlp2 * r + s_main.bytes[0] * r^2 + key_bytes[0] * r^3 + ... + key_bytes[key_len-1] * r^{key_len + 2}
```

So the multiplier to be used in the next row is `r^{key_len + 2}`. 

`mult_diff` needs to correspond to the key length + 2 RLP bytes + 1 byte for byte that contains the key length.
That means `mult_diff` needs to be `r^{key_len+1}` where `key_len = s_main.bytes[0] - 128`.

Note that the key length is different than the on of the leaf before it drifted (by one nibble
if a branch is added, by multiple nibbles if extension node is added).

### Account drifted leaf key RLC

#### Drifted leaf key RLC same as the RLC of the leaf before drift

The key RLC of the drifted leaf needs to be the same as the key RLC of the leaf before
the drift - the nibbles are the same in both cases, the difference is that before the
drift some nibbles are stored in the leaf key, while after the drift these nibbles are used as 
position in a branch or/and nibbles of the extension node.

### Account leaf key in added branch: drifted leaf hash in the parent branch

We take the leaf RLC computed in the key row, we then add nonce/balance and storage root/codehash
to get the final RLC of the drifted leaf. We then check whether the drifted leaf is at
the `drifted_pos` in the parent branch - we use a lookup to check that the hash that
corresponds to this RLC is in the parent branch at `drifted_pos` position.

### Range lookups

Range lookups ensure that the value in the columns are all bytes (between 0 - 255).
Note that `c_main.bytes` columns are not used.

## Account leaf non-existing-account constraints

The rows of the account leaf are the following:
```
ACCOUNT_LEAF_KEY_S
ACCOUNT_LEAF_KEY_C
ACCOUNT_NON_EXISTING
ACCOUNT_LEAF_NONCE_BALANCE_S
ACCOUNT_LEAF_NONCE_BALANCE_C
ACCOUNT_LEAF_STORAGE_CODEHASH_S
ACCOUNT_LEAF_STORAGE_CODEHASH_C
ACCOUNT_DRIFTED_LEAF
```

The constraints in this file apply to ACCOUNT_NON_EXISTING.

For example, the row might be:
```
[0,0,0,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```

We are proving that there is no account at the specified address. There are two versions of proof:
    1. A leaf is returned by getProof that is not at the required address (we call this a wrong leaf).
    In this case, the `ACCOUNT_NON_EXISTING` row contains the nibbles of the address (the nibbles that remain
    after the nibbles used for traversing through the branches are removed) that was enquired
    while `ACCOUNT_LEAF_KEY` row contains the nibbles of the wrong leaf. We need to prove that
    the difference is nonzero. This way we prove that there exists some account which has some
    number of the starting nibbles the same as the enquired address (the path through branches
    above the leaf), but at the same time the full address is not the same - the nibbles stored in a leaf differ.
    2. A branch is the last element of the getProof response and there is a nil object
    at the address position. Placeholder account leaf is added in this case.
    In this case, the `ACCOUNT_NON_EXISTING` row contains the same nibbles as `ACCOUNT_LEAF_KEY` and it is not needed. We just need to prove that the branch contains nil object (128) at the enquired address.

The whole account leaf looks like:
```
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
[0,0,0,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
[184,70,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
[184,70,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]
[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

Lookups:
The `non_existing_account_proof` lookup is enabled in `ACCOUNT_NON_EXISTING` row.
```

For the example of non-existing account proof account leaf see below:

```
[248 102 157 55 236 125 29 155 142 209 241 75 145 144 143 254 65 81 209 56 13 192 157 236 195 213 73 132 11 251 149 241 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 6]
[248 102 157 55 236 125 29 155 142 209 241 75 145 144 143 254 65 81 209 56 13 192 157 236 195 213 73 132 11 251 149 241 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 4]
[1 0 0 56 133 130 180 167 143 97 28 115 102 25 94 62 148 249 8 6 55 244 16 75 187 208 208 127 251 120 61 73 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 18]
[184 70 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 248 68 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 7]
[184 70 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 248 68 128 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 8]
[0 160 112 158 181 221 162 20 124 79 184 25 162 13 167 162 146 25 237 242 59 120 184 154 118 137 92 181 187 152 115 82 223 48 0 160 7 190 1 231 231 32 111 227 30 206 233 26 215 93 173 166 90 214 186 67 58 230 71 161 185 51 4 105 247 198 103 124 0 9]
[0 160 112 158 181 221 162 20 124 79 184 25 162 13 167 162 146 25 237 242 59 120 184 154 118 137 92 181 187 152 115 82 223 48 0 160 7 190 1 231 231 32 111 227 30 206 233 26 215 93 173 166 90 214 186 67 58 230 71 161 185 51 4 105 247 198 103 124 0 11]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 10]
```

In this case, the nibbles in the third row are different from the nibbles in the first or second row. Here, we are
proving that the account does not exist at the address which starts with the same nibbles as the leaf that is
in the rows above (except for the `ACCOUNT_NON_EXISTING` row) and continues with nibbles `ACCOUNT_NON_EXISTING` row.

Note that the selector (being 1 in this case) at `s_main.rlp1` specifies whether it is wrong leaf or nil case.

Lookups:
The `is_non_existing_account_proof` lookup is enabled in `ACCOUNT_NON_EXISTING` row.

### Non existing account proof leaf address RLC (leaf not in first level, branch not placeholder)

#### Account leaf key acc s_advice1

If there is an even number of nibbles stored in a leaf, `s_advice1` needs to be 32.

#### Account address RLC

Differently as for the other proofs, the account-non-existing proof compares `address_rlc` with the address
stored in `ACCOUNT_NON_EXISTING` row, not in `ACCOUNT_LEAF_KEY` row.

The crucial thing is that we have a wrong leaf at the address (not exactly the same, just some starting
set of nibbles is the same) where we are proving there is no account.
If there would be an account at the specified address, it would be positioned in the branch where
the wrong account is positioned. Note that the position is determined by the starting set of nibbles.
Once we add the remaining nibbles to the starting ones, we need to obtain the enquired address.
There is a complementary constraint that makes sure the remaining nibbles are different for wrong leaf
and the non-existing account (in the case of wrong leaf, while the case with nil being in branch
is different).

#### Wrong leaf sum check

We compute the RLC of the key bytes in the `ACCOUNT_NON_EXISTING` row. We check whether the computed
value is the same as the one stored in `accs.key.rlc` column.

#### Wrong leaf sum_prev check

We compute the RLC of the key bytes in the `ACCOUNT_NON_EXISTING` row. We check whether the computed
value is the same as the one stored in `accs.key.mult` column.

#### Address of a leaf is different than address being inquired (corresponding to address_rlc)

The address in the `ACCOUNT_LEAF_KEY` row and the address in the `ACCOUNT_NON_EXISTING` row
are indeed different.

#### Nil object in parent branch

In case when there is no wrong leaf, we need to check there is a nil object in the parent branch.
Note that the constraints in `branch.rs` ensure that `sel1` is 1 if and only if there is a nil object
at `modified_node` position. We check that in case of no wrong leaf in
the non-existing-account proof, `sel1` is 1.

### Non existing account proof leaf address RLC

Ensuring that the account does not exist when there is only one account in the state trie.
Similarly as `Account address RLC` constraint but for the first level.

Note 1: The hash of the only account is checked to be the state root in `account_leaf_storage_codehash.rs`.
Note 2: There is no nil_object case checked in this gate, because it is covered in the gate
above. That is because when there is a branch (with nil object) in the first level,
it automatically means the account leaf is not in the first level.

### Non existing account proof leaf address RLC (leaf in first level)

Similarly as the gate above, but for the account leaf being in the first level.

### Address of wrong leaf and the enquired address are of the same length

#### The number of nibbles in the wrong leaf and the enquired address are the same

This constraint is to prevent the attacker to prove that some account does not exist by setting
some arbitrary number of nibbles in the account leaf which would lead to a desired RLC.

### s_main.bytes[i] = 0 when key ends

Key RLC is computed over all of `s_main.bytes[1], ..., s_main.bytes[31], c_main.rlp1, c_main.rlp2`
because we do not know the key length in advance.
To prevent changing the key and setting `s_main.bytes[i]` (or `c_main.rlp1/c_main.rlp2`) for
`i > key_len + 1` to get the desired key RLC, we need to ensure that
`s_main.bytes[i] = 0` for `i > key_len + 1`.

Note that the number of the key bytes in the `ACCOUNT_NON_EXISTING` row needs to be the same as
the number of the key bytes in the `ACCOUNT_LEAF_KEY` row.

Note: the key length is always in s_main.bytes[0] here as opposed to storage
key leaf where it can appear in `s_rlp2` too. This is because the account
leaf contains nonce, balance, ... which makes it always longer than 55 bytes,
which makes a RLP to start with 248 (`s_rlp1`) and having one byte (in `s_rlp2`)
for the length of the remaining stream.

### Range lookups

Range lookups ensure that `s_main`, `c_main.rlp1`, `c_main.rlp2` columns are all bytes (between 0 - 255).
Note that `c_main.bytes` columns are not used.


## Example

Let us observe the proof for the modification of the account nonce. Let us assume there is only
one account stored in the trie. We change the nonce for this account from 0 to 1.

An account leaf occupies 8 rows. Thus, in our example, where there is only one account in the trie,
our circuit will only have 8 rows.

The witness for our proof looks like (excluding selector columns):

```
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[0,0,0,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[184,70,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[184,70,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,248,68,128,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]

[0,160,86,232,31,23,27,204,85,166,255,131,69,230,146,192,248,110,91,72,224,27,153,108,173,192,1,98,47,181,227,99,180,33,0,160,197,210,70,1,134,247,35,60,146,126,125,178,220,199,3,192,229,0,182,83,202,130,39,59,123,250,216,4,93,133,164,122]

[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```

The rows are:
```
ACCOUNT_LEAF_KEY_S
ACCOUNT_LEAF_KEY_C
ACCOUNT_NON_EXISTING
ACCOUNT_LEAF_NONCE_BALANCE_S
ACCOUNT_LEAF_NONCE_BALANCE_C
ACCOUNT_LEAF_STORAGE_CODEHASH_S
ACCOUNT_LEAF_STORAGE_CODEHASH_C
ACCOUNT_DRIFTED_LEAF
```

In `ACCOUNT_LEAF_NONCE_BALANCE_S` row, there is `S` nonce stored in `s_main`
and `S` balance in `c_main`. We can see nonce in `S` proof is `0 = 128 - 128`.

In `ACCOUNT_LEAF_NONCE_BALANCE_C` row, there is `C` nonce stored in `s_main`
and `C` balance in `c_main`. We can see nonce in `C` proof is `1`.

The two main things the circuit needs to check are:
 * Everything is the same in `S` and `C`, except the nonce value.
 * The change occurs at the proper account address.

However, there are many other things to be checked, for example the RLP encoding and RLC accumulators.
The RLC accumulators are used to compute the RLC of the whole node, in this particular case the RLC of
the account leaf. As the account leaf is distributed over multiple rows, we need to compute
the intermediate RLC in each row. That means we compute the RLC after the first row, then starts
with this value in the second row, compute the RLC after the second row:

```
account_s_rlc = account_leaf_key_s_rlc + account_leaf_nonce_balance_s_rlc * mult1 + account_leaf_storage_codehash_s_rlc * mult2
```

Note that `mult1` and `mult2` depend on the number of bytes in `account_leaf_key_s` and
`account_leaf_nonce_balance_s` bytes respectively. The RLC computed after the last row
and the RLC of the state trie hash (we only have this account in the trie) need
to be in the keccak table in the same row.

When we check that the computed account address is the same as the given address where the change
should occur, all address nibles are in the account leaf (no nibbles used in the branches as there
are no branches).
We can see this in the `ACCOUNT_LEAF_KEY_S` row:

```
[248,106,161,32,252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```

There are `33 = 161 - 128` bytes that store the nibbles. The value 32 does not hold any nibble
(this is how nibbles are compressed in case of even nibbles), but then we have 32 bytes that
store the nibbles:
```
[252,237,52,8,133,130,180,167,143,97,28,115,102,25,94,62,148,249,8,6,55,244,16,75,187,208,208,127,251,120,61,73]
```

Each of these bytes stores two nibbles. The address is computed as:
```
address_rlc = 252 + 237 * r + ... + 73 * r^31
```