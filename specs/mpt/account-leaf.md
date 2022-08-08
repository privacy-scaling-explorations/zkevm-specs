# Account leaf

## Nonce balance constraints

Let us observe the proof for the modification of the account nonce. Let us assume there is only
one account stored in the trie. We change the nonce for this account from 0 to 1.

An account leaf occupies 8 rows. Thus, in our example, where there is only one account in the trie,
our circuit will only have 8 rows.

Contrary as in the branch rows, the `S` and `C` leaves are not positioned parallel to each
other. The rows are the following:

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

In `ACCOUNT_LEAF_NONCE_BALANCE_S` row, there is `S` nonce stored in `s_main` and `S` balance in
`c_main`. We can see nonce in `S` proof is `0 = 128 - 128`.

In `ACCOUNT_LEAF_NONCE_BALANCE_C` row, there is `C` nonce stored in `s_main` and `C` balance in
`c_main`. We can see nonce in `C` proof is `1`.

The two main things the circuit needs to check are:
 * Everything is the same in `S` and `C`, except the nonce value.
 * The change occurs at the proper account address.

However, there are many other things to be checked, for example the RLP encoding and RLC accumulators.
The RLC accumulators are used to compute the RLC of the whole node, in this particular case, the RLC of
the account leaf. As an account leaf is distributed over multiple rows, we need to compute the intermediate
RLC in each row.

All chips in the MPT circuit use the first gate to check the RLP encoding,
the computation of RLC, and selectors being of proper values (for example being
boolean).

The constraints for the first gate of `AccountLeafNonceBalanceChip` which is named
`Account leaf nonce balance RLC & RLP` are given below.

### Bool check is_nonce_long & Bool check is_balance_long

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

### s_main.bytes[i] = 0 for i > 0 when is_nonce_short

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

### c_main.bytes[i] = 0 for i > 0 when is_balance_short

The balance constraints are analogous to the nonce constraints described above.
The difference is that balance is stored in `c_main.bytes`.

### is_wrong_leaf is bool

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

### is_wrong_leaf needs to be 0 when not in non_existing_account proof

`is_wrong_leaf` can be set to 1 only when the proof is not non_existing_account proof.

### Nonce RLC long 

Besides having nonce (its bytes) stored in `s_main.bytes`, we also have the RLC
of nonce bytes stored in `s_mod_node_hash_rlc` column. The value in this column
is to be used by lookups.
`Nonce RLP long` constraint ensures the RLC of a nonce is computed properly when
nonce is long.

### Nonce RLC short

Similarly as in `Nonce RLP long` constraint, 
`Nonce RLP short` constraint ensures the RLC of a nonce is computed properly when
nonce is short.

### Balance RLC long 

Besides having balance (its bytes) stored in `c_main.bytes`, we also have the RLC
of nonce bytes stored in `c_mod_node_hash_rlc` column. The value in this column
is to be used by lookups.
`Balance RLP long` constraint ensures the RLC of a balance is computed properly when
balance is long.

### Balance RLC short

Similarly as in `Balance RLP long` constraint, 
`Balance RLP short` constraint ensures the RLC of a balance is computed properly when
balance is short.

### S nonce RLC is correctly copied to C row

To enable lookup for nonce modification we need to have `S` nonce and `C` nonce
in the same row. For this reason, `S` nonce RLC is copied to `sel1` column in `C` row.
This constraint checks whether the value is properly copied.

### S balance RLC is correctly copied to C row

To enable lookup for balance modification we need to have `S` balance and `C` balance
in the same row. For this reason, `S` balance RLC is copied to `sel2` column in `C` row.
This constraint checks whether the value is properly copied.

### If storage or balance modification: S nonce = C nonce

We need to ensure there is only one modification at a time. If there is storage or
balance modification, we need to ensure `S` nonce and `C` nonce are the same.

### If storage or nonce modification: S balance = C balance

We need to ensure there is only one modification at a time. If there is storage or
nonce modification, we need to ensure `S` balance and `C` balance are the same.

### Leaf nonce acc mult (nonce long)

When adding nonce bytes to the account leaf RLC we do:
`rlc_after_nonce = rlc_tmp + s_main.bytes[0] * mult_tmp + s_main.bytes[1] * mult_tmp * r + ... + s_main.bytes[k] * mult_tmp * r^k`
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
`rlc_after_nonce = rlc_tmp + s_main.rlp1 * mult_tmp + s_main.rlp2 * mult_tmp * r + c_main.rlp1 * mult_tmp * r^2 + c_main.rlp2 * mult_tmp * r^3 + s_main.bytes[0] * mult_tmp * r^4 + ... + s_main.bytes[k] * mult_tmp * r^4 * r^k`
That means `mult_diff_nonce` needs to store `r^4 * r^{k+1}` and we continue computing the RLC
as mentioned above:
`rlc_after_nonce + b1 * mult_tmp * mult_diff_nonce + b2 * mult_tmp * mult_diff_nonce * r + ...

Let us observe the following example.
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
Here:
`rlc_after_nonce = rlc_tmp + 184 * mult_tmp + 78 * mult_tmp * r + 248 * mult_tmp * r^2 + 76 * mult_tmp * r^3 + 129 * mult_tmp * r^4 + 142 * mult_tmp * r^5`
And we continue computing the RLC:
`rlc_after_nonce + 135 * mult_tmp * mult_diff_nonce + 28 + mult_tmp * mult_diff_nonce * r + ... `

### Leaf nonce acc mult (nonce short)

When nonce is short (occupying only one byte), we know in advance that `mult_diff_nonce = r^5`
as there are `s_main.rlp1`, `s_main.rlp2`, `c_main.rlp1`, `c_main.rlp2`, and `s_main.bytes[0]` bytes to be taken into account.

### Leaf balance acc mult (balance long)

We need to prepare the multiplier that will be needed in the next row: `acc_mult_final`.
We have the multiplier after nonce bytes were added to the RLC: `acc_mult_after_nonce`.
Now, `acc_mult_final` depends on the number of balance bytes. 
`rlc_after_balance = rlc_after_nonce + b1 * acc_mult_after_nonce + ... + bl * acc_mult_after_nonce * r^{l-1}`
Where `b1,...,bl` are `l` balance bytes. As with nonce, we do not know the length of balance bytes
in advance. For this reason, we store `r^l` in `mult_diff_balance` and check whether:
`acc_mult_final = acc_mult_after_nonce * mult_diff_balance`.
Note that `mult_diff_balance` is not the last multiplier in this row, but the first in
the next row (this is why there is `r^l` instead of `r^{l-1}`).

### Leaf balance acc mult (balance short)

When balance is short, there is only one balance byte and we know in advance that the
multiplier changes only by factor `r`.

### Leaf nonce balance s_main.rlp1 = 184

`s_main.rlp1` needs always be 184. This is RLP byte meaning that behind this byte
there is a string of length more than 55 bytes and that only `1 = 184 - 183` byte is reserved
for length (`s_main.rlp2`). The string is always of length greater than 55 because there
are codehash (32 bytes) and storage root (32 bytes) in the next row as part of this string.

The only exception is when `is_non_existing_account_proof = 1` & `is_wrong_leaf = 0`.
In this case the value does not matter as the account leaf is only a placeholder and
does not use `s_main.rlp1` and `s_main.rlp2`. Note that it uses `s_main` for nibbles
because the account address is computed using nibbles and this account address needs
to be as required by a lookup.

### Leaf nonce balance c_main.rlp1 = 248

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

### Leaf nonce balance s_main.rlp2 - c_main.rlp2

`c_main.rlp2` specifies the length of the remaining RLP string. Note that the string
is `s_main.rlp1`, `s_main.rlp2`, `c_main.rlp1`, `c_main.rlp2`, nonce bytes, balance bytes.
Thus, `c_main.rlp2 = #(nonce bytes) + #(balance bytes) + 32 + 32`.
`s_main.rlp2` - `c_main.rlp2` = 2 because of two bytes difference: `c_main.rlp1` and c_main.rlp2`.

Example:
```
[184  78   129      142       0 0 ... 0 248  76   135      28       5 107 201 118 120 59 0 0 ... 0]
```
We can see: `78 - 76 - 1 - 1 = 0`.

### Lean nonce balance c_main.rlp2

`c_main.rlp2 = #(nonce bytes) + #(balance bytes) + 32 + 32`.
Note that `32 + 32` means the number of codehash bytes + the number of storage root bytes.

### Account leaf RLP length 

The whole RLP length of the account leaf is specified in the account leaf key row with
`s_main.rlp1 = 248` and `s_main.rlp2`. `s_main.rlp2` in key row actually specifies the length.
`s_main.rlp2` in nonce balance row specifies the length of the remaining string in nonce balance
row, so we need to check that `s_main.rlp2` corresponds to the key length (in key row) and
`s_main.rlp2` in nonce balance row. However, we need to take into account also the bytes
where the lengths are stored:
`s_main.rlp2 (key row) - key_len - 1 (because key_len is stored in 1 byte) - s_main.rlp2 (nonce balance row) - 1 (because of s_main.rlp1) - 1 (because of s_main.rlp2) = 0`

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

## Storage codehash constraints

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

### Account leaf storage codehash s_main.rlp2 = 160

`s_main.rlp2` stores the RLP length of the hash of storage root. The hash output length is 32
and thus `s_main.rlp2` needs to be `160 = 128 + 32`. 

### Account leaf storage codehash c_main.rlp2 = 160

`c_main.rlp2` stores the RLP length of the codehash. The hash output length is 32
and thus `c_main.rlp2` needs to be `160 = 128 + 32`. 

### Storage root RLC 

`s_main.bytes` contain storage root hash, but to simplify lookups we need to have
the RLC of storage root hash stored in some column too. The RLC is stored in
`s_mod_node_hash_rlc`. We need to ensure that this value corresponds to the RLC
of `s_main.bytes`.

### Codehash RLC

`c_main.bytes` contain codehash, but to simplify lookups we need to have
the RLC of the codehash stored in some column too. The RLC is stored in
`c_mod_node_hash_rlc`. We need to ensure that this value corresponds to the RLC
of `c_main.bytes`.

### S storage root RLC is correctly copied to C row

To enable lookup for storage root modification we need to have S storage root
and C storage root in the same row.
For this reason, S storage root RLC is copied to `sel1` column in C row.

Note: we do not need such constraint for codehash as the codehash never changes.

### If nonce / balance: storage_root_s = storage_root_c

If the modification is nonce or balance modification, the storage root needs to 
stay the same.

Note: `is_non_existing_account_proof` uses only `S` proof.

### If nonce / balance / storage mod: codehash_s = codehash_c

If the modification is nonce or balance or storage modification (that means
always except for `is_account_delete_mod` and `is_non_existing_account_proof`),
the storage root needs to stay the same.

Note: `is_non_existing_account_proof` uses only `S` proof.

### Account leaf storage codehash RLC

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


