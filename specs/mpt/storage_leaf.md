# Storage leaf

A storage leaf occupies 5 rows.
Contrary as in the branch rows, the `S` and `C` leaves are not positioned parallel to each other.
The rows are the following:
```
LEAF_KEY_S
LEAF_VALUE_S
LEAF_KEY_C
LEAF_VALUE_C
LEAF_DRIFTED
```

An example of leaf rows:
```
[226 160 59 138 106 70 105 186 37 13 38 205 122 69 158 202 157 33 95 131 7 227 58 235 229 3 121 188 90 54 23 236 52 68 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2]
[1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 13]
[226 160 59 138 106 70 105 186 37 13 38 205 122 69 158 202 157 33 95 131 7 227 58 235 229 3 121 188 90 54 23 236 52 68 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3]
[17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 14]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 15]
```

In the above example the value has been changed from 1 (`LEAF_VALUE_S`) to 17 (`LEAF_VALUE_C`).

In the example below the value in `LEAF_VALUE_C` takes more than 1 byte: `[187 239 170 ...]`
This has two consequences:
 - Two additional RLP bytes: `[161 160]` where `33 = 161 - 128` means there are `31` bytes behind `161`,
   `32 = 160 - 128` means there are `30` bytes behind `160`.
 - `LEAF_KEY_S` starts with `248` because the leaf has more than 55 bytes, `1 = 248 - 247` means
   there is 1 byte after `248` which specifies the length - the length is `67`. We can see that
   that the leaf key is shifted by 1 position compared to the example above.

For this reason we need to distinguish two cases: 1 byte in leaf value, more than 1 byte in leaf value.
These two cases are denoted by `is_short` and `is_long`. There are two other cases we need to
distinguish: `last_level` when the leaf is in the last level and has no nibbles, `one_nibble` when
the leaf has only one nibble.

`last_level`:
```
[226 160 59 138 106 70 105 186 37 13 38 205 122 69 158 202 157 33 95 131 7 227 58 235 229 3 121 188 90 54 23 236 52 68 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2]
[1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 13]
[248 67 160 59 138 106 70 105 186 37 13 38 205 122 69 158 202 157 33 95 131 7 227 58 235 229 3 121 188 90 54 23 236 52 68 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3]
[161 160 187 239 170 18 88 1 56 188 38 60 149 117 120 38 223 78 36 235 129 201 170 170 170 170 170 170 170 170 170 170 170 170 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 14]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 15]
```

`last_level`
```
[194 32 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2]
[1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 13]
[194 32 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3]
[17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 14]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 15]
```

`one_nibble`:
```
[194 48 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2]
[1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 13]
[194 48 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3]
[17 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 14]
[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 15]
```

`s_mod_node_rlc` (`flag1`) and `c_mod_node_rlc` (`flag2`) columns store the information of what
kind of case we have:
 `flag1: 1, flag2: 0`: `is_long`
 `flag1: 0, flag2: 1`: `is_short`
 `flag1: 1, flag2: 1`: `last_level`
 `flag1: 0, flag0: 1`: `one_nibble`

The constraints in `leaf_key.rs` apply to `LEAF_KEY_S` and `LEAF_KEY_C` rows.

## Storage leaf key constraints

### Storage leaf key RLC

#### is_long: s_rlp1 = 248

When `is_long` (the leaf value is longer than 1 byte), `s_main.rlp1` needs to be 248.

Example:
`[248 67 160 59 138 106 70 105 186 37 13 38 205 122 69 158 202 157 33 95 131 7 227 58 235 229 3 121 188 90 54 23 236 52 68 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3]`

#### last_level: s_rlp2 = 32

When `last_level`, there is no nibble stored in the leaf key, it is just the value
`32` in `s_main.rlp2`. In the `getProof` output, there is then the value stored immediately
after `32`. However, in the MPT witness, we have value in the next row, so there are 0s
in `s_main.bytes` (we do not need to check `s_main.bytes[i]` to be 0 due to how the RLC
constraints are written).

Example:
`[194 32 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3]`

#### flag1 is boolean & flag2 is boolean

The two values that store the information about what kind of case we have need to be boolean.

#### Leaf key RLC (short or long)

We need to ensure that the RLC of the row is computed properly for `is_short` and
`is_long`. We compare the computed value with the value stored in `accumulators.acc_s.rlc`.

#### Leaf key RLC (last level or one nibble)

We need to ensure that the RLC of the row is computed properly for `last_level` and
`one_nibble`. We compare the computed value with the value stored in `accumulators.acc_s.rlc`.

`last_level` and `one_nibble` cases have one RLP byte (`s_rlp1`) and one byte (`s_rlp2`)
where it is 32 (for `last_level`) or `48 + last_nibble` (for `one_nibble`).

#### 0s after the last key nibble

There are 0s in `s_main.bytes` after the last key nibble (this does not need to be checked for `last_level` and `one_nibble` as in these cases `s_main.bytes` are not used).

### mult_diff

The intermediate RLC value of this row is stored in `accumulators.acc_s.rlc`.
To compute the final leaf RLC in `LEAF_VALUE` row, we need to know the multiplier to be used
for the first byte in `LEAF_VALUE` row too. The multiplier is stored in `accumulators.acc_s.mult`.
We check that the multiplier corresponds to the length of the key that is stored in `s_main.rlp2`
for `is_short` and in `s_main.bytes[0]` for `is_long`.

Note: `last_level` and `one_nibble` have fixed multiplier because the length of the nibbles
in these cases is fixed.

### Storage leaf key RLC & nibbles count (leaf not in first level, branch not placeholder)

We need to ensure that the storage leaf is at the key specified in `key_rlc` column (used
by MPT lookup). To do this we take the key RLC computed in the branches above the leaf
and add the remaining bytes (nibbles) stored in the leaf.

We also ensure that the number of all nibbles (in branches / extension nodes above
the leaf and in the leaf) is 64.

#### Leaf key RLC s_bytes0 = 32 (short)

If `c1` and branch above is not a placeholder, we have 32 in `s_main.bytes[0]`.
This is because `c1` in the branch above means there is an even number of nibbles left
and we have an even number of nibbles in the leaf, the first byte (after RLP bytes
specifying the length) of the key is 32.

#### Key RLC (short)

We need to ensure the leaf key RLC is computed properly. We take the key RLC value
from the last branch and add the bytes from position
`s_main.bytes[0]` up at most to `c_main.rlp1`. We need to ensure that there are 0s
after the last key byte, this is done by `key_len_lookup`.

The computed value needs to be the same as the value stored `key_rlc` column.

`is_short` example:
[226,160,59,138,106,70,105,186,37,13,38[227,32,161,160,187,239,170,18,88,1,56,188,38,60,149,117,120,38,223,78,36,235,129,201,170,170,170,170,170,170,170,170,170,170,170,170]

Note: No need to distinguish between `c16` and `c1` here as it was already
when computing `key_rlc_acc_short`.

#### Leaf key acc s_bytes1 = 32 (long)

If `c1` and branch above is not a placeholder, we have 32 in `s_main.bytes[1]`.
This is because `c1` in the branch above means there is an even number of nibbles left
and we have an even number of nibbles in the leaf, the first byte (after RLP bytes
specifying the length) of the key is 32.

#### Key RLC (long)

We need to ensure the leaf key RLC is computed properly. We take the key RLC value
from the last branch and add the bytes from position
`s_main.bytes[1]` up at most to `c_main.rlp2`. We need to ensure that there are 0s
after the last key byte, this is done by `key_len_lookup`.

The computed value needs to be the same as the value stored `key_rlc` column.

`is_long` example:
`[248,67,160,59,138,106,70,105,186,37,13,38,205,122,69,158,202,157,33,95,131,7,227,58,235,229,3,121,188,90,54,23,236,52,68,161,160,...`

Note: No need to distinguish between `c16` and `c1` here as it was already
when computing `key_rlc_acc_long`.

#### Key RLC (last level)

We need to ensure the leaf key RLC is computed properly.
When the leaf is in the last level we simply take the key RLC value
from the last branch and this is the final key RLC value as there is no
nibble in the leaf.

The computed value needs to be the same as the value stored `key_rlc` column.

Last level example:
`[227,32,161,160,187,239,170,18,88,1,56,188,38,60,149,117,120,38,223,78,36,235,129,201,170,170,170,170,170,170,170,170,170,170,170,170]`

#### Key RLC (one nibble)

We need to ensure the leaf key RLC is computed properly.
When there is only one nibble in the leaf, we take the key RLC value
from the last branch and add the last remaining nibble stored in `s_main.rlp2`.

The computed value needs to be the same as the value stored `key_rlc` column.

One nibble example short value:
`[194,48,1]`

One nibble example long value:
`[227,48,161,160,187,239,170,18,88,1,56,188,38,60,149,117,120,38,223,78,36,235,129,201,170,170,170,170,170,170,170,170,170,170,170,170]`

####


