# Exponentiation Proof Design Document

The Exponentiation Circuit is a sub-circuit within the [`SuperCircuit`](https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/main/zkevm-circuits/src/super_circuit.rs) used to validate exponentiation, particularly required for the [`EXP`](https://www.evm.codes/playground?unit=Wei&codeType=Mnemonic&code=%27z1~2~10wyyz2~2~2w%27~yPUSH1%20z%2F%2F%20Example%20y%5CnwyEXP%01wyz~_) opcode gadget within the [`EVM Circuit`](https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/main/zkevm-circuits/src/evm_circuit.rs).

## Why a separate sub-circuit

For most EVM opcodes that are decomposed into multiple steps, we use the [`Copy Circuit`](https://github.com/privacy-scaling-explorations/zkevm-circuits/blob/main/zkevm-circuits/src/copy_circuit.rs). Examples are `CALLDATACOPY`, `CODECOPY`, `SHA3`, `RETURN`, `LOG` to name a few.

The copy circuit is designed to support read-write operations at every internal step, which for instance could be memory read, memory write, tx lookups, etc.

In a similar way, the exponentiation operation can be decomposed into steps for exponentiation by squaring. However there are no read-write operations or lookups to any other table. Instead, at every step we must validate whether the multiplication was done appropriately.

In order to separate these concerns and not complicate the constraints for the copy circuit, I believe it makes more sense to implement a separate sub-circuit to verify the exponentiation operation.

## Background

Define the exponentiation operation as:
```
base ^ exponent == exponentiation (mod 2^256)
```
where `base`, `exponent` and `exponentiation` are 256-bit EVM words.

We define _exponentiation by squaring_ with the following pseudocode:
```
Function exp_by_squaring(x, n, intermediate_steps)
    if n = 0  then return  1;
    if n = 1  then return  x; 
    
    exp1 = exp_by_squaring(x, n // 2)
    exp2 = exp1 * exp1
    intermediate_steps.append((exp1, exp1, exp2))
    
    if n is even:
        return exp2
    if n is odd:
        exp = x * exp2
        intermediate_steps.append((exp2, x, exp))
        return exp
```

For instance, consider the operation `3 ^ 13 == 1594323 (mod 2^256)`. This can be decomposed into the following multiplication steps:
```
3      * 3   == 9
9      * 3   == 27
27     * 27  == 729
729    * 729 == 531441
531441 * 3   == 1594323
```

Each of the above multiplication steps can be defined as:
```
a * b + c == d (mod 2^256)
```
where `a`, `b`, `c` and `d` are each 256-bit words and we have `c == 0`. We build and use a `MulAddGadget` to validate each of the steps.

Considering each of the above steps, we have:
* For the first step:
    * `a == b == base`
* For the last step:
    * `d == exponentiation`

***Note***: We will eventually populate our circuit with these steps in the reverse order, so that at the last row, we have `a == b == base` and at the first row we have `d == exponentiation`.

--------------------------------------------------------

## Exponentiation Circuit Layout

Within the exponentiation circuit, our goal is to:
* Verify that each multiplication step is computed correctly.
* Verify that `c == 0` for each multiplication step.
* Verify that for the first multiplication (last row), `a == b == base`
* Verify that the intermediate exponentiation (each step of the _exponentiation by squaring_) is correct.
* Verify that the intermediate exponent is divided by 2 correctly to yield the said remainder.

We also use multiple rows for a single multiplication step to make the circuit prover-efficient, so to achieve this we use a selector `q_step` to mark any given row as the starting point of a step.

We use the following columns/gadgets in the exponentiation circuit:
##### Circuit
* `q_usable`: Selector which when enabled indicates that the row is used in the exponentiation circuit's layout.
##### Exponentiation Table (exp_table)
* `is_step`: A boolean value indicating whether this row is the first row from the set of rows representing a step from the exponentiation trace.
* `identifier`: An identifier to uniquely identify an exponentiation trace. As of now, we use the read-write counter after reading both stack elements as the identifier.
* `is_last`: Indicates whether or not the step is the last step for this exponentiation operation.
* `base_limbs`: Column (4 rows) for representing the `base` as 64-bit limbs.
* `exponent_lo_hi`: Column (2 rows) for representing the `exponent` as 128-bit low and high components.
* `exponentiation_lo_hi`: Column (2 rows) for representing the `exponentiation` result as 128-bit low and high components.
##### MulAddGadget (mul_gadget) for `a*b + c == d (mod 2^256)`
* `a_limbs[i]`: Four columns representing `a` as 64-bit limbs, used for each multiplication step.
* `b_limbs[i]`: Four columns representing `b` as 64-bit limbs, used for each multiplication step.
* `c_lo_hi[i]`: Two columns representing `c` as 128-bit low and high components. Both `c_lo` and `c_hi` are equal to `0`.
* `d_lo_hi[i]`: Two columns representing `d` as 128-bit low and high components.
##### MulAddGadget (parity_check) for `2*q + r == exponent (mod 2^256)`
* Similar as above, and `a == 2`, `c == 0`, `d == exponent`.

--------------------------------------------------------

### MulAddGadget

We use multiple rows to layout the `MulAddGadget` and it looks as follows:
| q_step | col0      | col1      | col2      | col3      | col4      |
|--------|-----------|-----------|-----------|-----------|-----------|
| 1      | a_limb0   | a_limb1   | a_limb2   | a_limb3   | -         |
| 0      | b_limb0   | b_limb1   | b_limb2   | b_limb3   | -         |
| 0      | c_lo      | c_hi      | d_lo      | d_hi      | -         |
| 0      | carry_lo0 | carry_lo1 | carry_lo2 | carry_lo3 | carry_lo4 |
| 0      | carry_lo5 | carry_lo6 | carry_lo7 | carry_lo8 | -         |
| 0      | carry_hi0 | carry_hi1 | carry_hi2 | carry_hi3 | carry_hi4 |
| 0      | carry_hi5 | carry_hi6 | carry_hi7 | carry_hi8 | -         |

So effectively we use a total of 5 columns, namely `col0`, `col1`, `col2`, `col3` and `col4`, while splitting the limbs of `a` and `b` and low-high components of `c` and `d` over consecutive rows. The `carry` fields are for handling carry-over values while computing the overflowing multiplication.

Effectively, the `MulAddGadget` consumes 7 rows per step.

--------------------------------------------------------

### Exponentiation Table

We use multiple rows to layout the `ExpTable` and it looks as follows:
| is_step | identifier | is_last | base_limb  | exponent_lo_hi | exponentiation_lo_hi |
|---------|------------|---------|------------|----------------|----------------------|
| 1       | $rwc       | 0       | base_limb0 | exponent_lo    | exponentiation_lo    |
| 0       | $rwc       | 0       | base_limb1 | exponent_hi    | exponentiation_hi    |
| 0       | $rwc       | 0       | base_limb2 | 0              | 0                    |
| 0       | $rwc       | 0       | base_limb3 | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 1       | $rwc       | 0       | base_limb0 | exponent_lo    | exponentiation_lo    |
| 0       | $rwc       | 0       | base_limb1 | exponent_hi    | exponentiation_hi    |
| 0       | $rwc       | 0       | base_limb2 | 0              | 0                    |
| 0       | $rwc       | 0       | base_limb3 | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| ...     | $rwc       | 0       | ...        | ...            | ...                  |
| 1       | $rwc       | 1       | base_limb0 | exponent_lo    | exponentiation_lo    |
| 0       | $rwc       | 0       | base_limb1 | exponent_hi    | exponentiation_hi    |
| 0       | $rwc       | 0       | base_limb2 | 0              | 0                    |
| 0       | $rwc       | 0       | base_limb3 | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |
| 0       | $rwc       | 0       | 0          | 0              | 0                    |

***Note 3***: The exponentiation table uses 4 rows to represent each step, however we pad 3 more rows since the `MulAddGadget` uses 7 rows per step.

We populate the exponentiation table in reverse order so that for the first row, we have:
```
is_step.       -> 1
base           -> base_limbs[0..4]
exponent       -> exponent_lo_hi[0..2]
exponentiation -> exponentiation_lo_hi[0..2]
```
and hence a lookup to the exponentiation table at this row confirms the presence of `base`, `exponent` and `exponentiation` for:
```
base ^ exponent == exponentiation (mod 2^256)
```

The `exponent` field is assigned a reducing value of the `exponent` such that:
* At the first step, `exponent == exponent`
* For all subsequent steps:
    * `exponent::cur == exponent::prev - 1` if `exponent::prev` is odd
    * `exponent::cur == exponent::prev // 2` if `exponent::prev` is even
    * `a == b` if `exponent` is even
    * `b == base` if `exponent` is odd
* At the last step, i.e. `is_last == 1`, we have:
    * `exponent::cur == 2`
    * `a == b == base`

The `exponentiation` field is defined as the result of the multiplication step, so we have:
* At the first row, `exponentiation == exponentiation`
* For every subsequent step:
    * `exponentiation::cur == mul_gadget.d`. But we represent the `exponentiation` value as two 128-bit low-high parts, hence:
        * `exponentiation_lo::cur == mul_gadget.d_lo`
        * `exponentiation_hi::cur == mul_gadget.d_hi`

--------------------------------------------------------

## `EXP` Opcode Gadget

The `EXP` opcode's gadget is within the `EVM Circuit`.

It uses the following columns:
* `base`: RLC-encoded 32-byte word, popped from the stack
* `exponent`: RLC-encoded 32-byte word, popped from the stack
* `exponentiation`: RLC-encoded 32-byte word, pushed to the stack
* `exponent_is_zero`: `IsZeroGadget` to check whether or not `exponent == 0`
* `exponent_is_one`: `IsEqualGadget` to check whether or not `exponent == 1`
* `single_step`: A boolean to indicate whether or not there will be a single step in the exponentiation trace. There is a single step if `exponent == 2`, which means we have `base * base == base^2 (mod 2^256)` as the only step. We use this to determine the `is_first` and `is_last` column values, while doing lookups to the exponentiation table.
* `exponent_byte_size`: `ByteSizeGadget` to check the byte-size of `exponent`, i.e. the minimum number of bytes that are required to represent `exponent`. In python, the code for byte size would be:
```
byte_size_value = (value.bits() + 7) // 8
```

### Constraints

* If `exponent == 0` then `exponentiation == 1`
* If `exponent == 1` then `exponentiation == base`
* If `exponent == 2` then:
    * Do lookup to the `ExpTable`:
    ```
    (
        is_last=1,
        base_limbs,
        exponent_lo_hi,
        exponentiation_lo_hi
    )
    ```
* If `exponent > 2` then:
    * Do lookup to the `ExpTable`:
    ```
    (
        is_last=0,
        base_limbs,
        exponent_lo_hi,
        exponentiation_lo_hi,
    )
    ```
    * Do lookup to the `ExpTable`:
    ```
    (
        is_last=1,
        base_limbs,
        exponent_lo_hi=[2, 0],
        exponentiation_lo_hi=[base_sq_lo, base_sq_hi],
    )
    ```
    where `base_sq_lo` and `base_sq_hi` are the 128-bit low-high parts of `base ^ 2 (mod 2^256)`.
* If `exponent == 0` then `exponent_byte_size == 0`
* Gas cost `gas == constant_gas_cost(EXP) +  dynamic_gas_cost` where `dynamic_gas_cost == 50 * exponent_byte_size`.

--------------------------------------------------------

## Byte Size Gadget

We wish to calculate an expression that represents the byte size of a 32-bytes RLC-encoded word.

We make use of an array of 33 cells, called `most_significant_nonzero_byte_index`. In this array, exactly one cell will be turned on (set to `1`) while the rest are all `0`. The turned on cell indicates the index of the most significant non-zero byte in the 32-bytes word.

If this index is such that `index > 0`, this means that the byte size is non-zero. Which also means that there exists an inverse of the byte at that index in the 32-bytes word.

We make use of a cell called `most_significant_nonzero_byte_inverse` to store the inverse of the byte at the said index.

### Constraints

* Exactly one cell is turned on from the array `most_significant_nonzero_byte_index`.
* For instance, if the above turned on index is `index'`, then we have:
```
sum(word_bytes[index'..32]) == 0
```
which basically means that, all the other bytes from `index'` must be `0` (since in the little-endian representation of word, bytes beyond the byte-size will be `0`).
* If `index' > 0` then:
```
word_bytes[index'] * most_significant_nonzero_byte_inverse == 1
```
