# Exponentiation Proof

The exponentiation proof validates entries in the exponentiation circuit, which includes the exponentiation table. Each `EXP` opcode performed in a block's transactions is mapped to an exponentiation trace, more specifically these are the intermediate multiplication steps produced while exponentiation by squaring.

For instance, `3 ^ 13 == 1594323 (mod 2^256)` is mapped to the following steps:
```
3      * 3   = 9
9      * 3   = 27
27     * 27  = 729
729    * 729 = 531441
531441 * 3   = 1594323
```

Moving on, we refer each of the above multiplication steps as:
```
a * b + c = d
```
while validating the equation using a `MulAddWordsGadget` where `c == 0`.

For a detailed algorithm, please refer the [design document](https://hackmd.io/@rohitnarurkar/BJhpYGiCc).

## Circuit Layout

The exponentiation circuit contains columns from the [exponentiation table](./tables.md#exponentiation-table) in addition to the following columns:
1. `q_step`: A selector to indicate whether or not the current row represents a step in the exponentiation trace.
2. `is_pad`: A boolean-valued advice column to indicate whether or not the step is reserved for padding or not.
3. `is_odd`: a boolean-valued advice column to indicate whether or not the exponent at this step is odd or even.
4. `fixed_table`: A set of 2 fixed columns spanning over 128 rows, reserved for odd/even byte-values. The odd table will consist of values `{1, 3, 5, ..., 253, 255}` and the even table will consist of values `{0, 2, 4, ..., 252, 254}`.

We even use a few columns to perform multiplication (modulo `2^256`) of the intermediate steps in the exponentiation trace.

## Circuit Constraints

- For every step except the last step, validate that:
    - `base` MUST be the same across subsequent steps.
    - Multiplication result `d` from the next row MUST be equal to the first multiplicand `a` in the current row. For instance, if we consider `row_0` (`531441 * 3 = 1594323`) and `row_1` (`729 * 729 = 531441`) from the above example, `d_1` is `531441` and `a_0` is also `531441`.

- For every step, validate that:
    - `is_first` and `is_last` MUST be boolean.
    - `is_first == 1` MUST be followed by `is_first::next == 0`.
    - `is_first == 0` MUST be followed by `is_first::next == 0`.
    - `is_last == 1` MUST be followed by a padding row, i.e. `is_pad::next == 1`.
    - The multiplication `a * b + c == d` MUST be assigned correctly, where `c == 0`.
    - At every intermediate step in the exponentiation trace, the `exponentiation` MUST be equal to `d`, which is the result of the multiplication.
    - `is_odd` MUST be boolean.

- For every step except the last step where `is_odd == 1`:
    - The second multiplicand in the multiplication `b` MUST be equal to `base`.
    - `exponent::next == exponent::cur - 1`, which implies:
        - `exponent_lo::next == exponent_lo::cur - 1`.
	- `exponent_hi::next == exponent_hi::cur`.

- For every step except the last step where `is_odd == 0`:
    - Both the multiplicands in the multiplication `a` and `b` MUST be equal, i.e. `a == b`.
    - `exponent::next == exponent::cur // 2`, which implies:
        - `exponent_lo::next * 2 == exponent_lo::cur`.
	- `exponent_hi::next * 2 == exponent_hi::cur`.

- For the last step in the exponentiation trace, i.e. `is_last == 1`:
    - The exponent has reduced to `2`, i.e. `exponent_lo == 2` and `exponent_hi == 0`.
    - Both multiplicands in the multiplication are equal to the `base` of the exponentiation operation, i.e. `a == b == base`.

## Code

Please refer to [Exponentiation Circuit Verification](`src/zkevm-specs/exp_circuit.py`).
