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

For a detailed algorithm, please refer the [design document](../specs/exp-proof-design-doc.md).

## Circuit Layout

The exponentiation circuit consists of the following columns:
1. `q_usable`: A selector to indicate whether or not the current row will be used in the circuit's layout.
2. `exp_table`: The columns from [exponentiation table](./tables.md#exponentiation-table)
3. `mul_gadget`: The columns from a multiplication gadget, responsible for validating that each step within the exponentiation trace was multiplied correctly. For instance, in the above example we would want to verify that `729 * 729 == 531441 (mod 2^256)`.
4. `parity_check`: The columns from a multiplication gadget, responsible for checking the parity (odd/even) of the `exponent` at the specific step of exponentiation trace. Depending on whether the `exponent` is odd or even, we calculate the `exponent` at the next step.

## Circuit Constraints

- For every row where `is_step == true`, except the last step, validate that:
    - `base` MUST be the same across subsequent steps.
    - Multiplication result `d` from the next row MUST be equal to the first multiplicand `a` in the current row. For instance, if we consider `row_0` (`531441 * 3 = 1594323`) and `row_1` (`729 * 729 = 531441`) from the above example, `d_1` is `531441` and `a_0` is also `531441`.
    - `identifier` MUST be the same across subsequent steps, i.e. `identifier::cur_step == identifier::next_step`.

- For every row, validate that:
    - `exp_table.is_step` MUST be boolean.
    - `exp_table.is_last` MUST be boolean.

- For every row where `is_step == true`, validate that:
    - `exponentiation_lo` MUST equal `mul_gadget`'s multiplication result `d_lo`.
    - `exponentiation_hi` MUST equal `mul_gadget`'s multiplication result `d_hi`.
    - Since we are only performing multiplication with the equation `a * b + c == d`, `c` in the `mul_gadget` MUST equal `0`.
    - Since we are performing `2 * q + r == exponent` in the `parity_check` multiplication gadget, `r` is boolean, that is:
        - `r_hi` MUST equal `0`.
        - `r_lo` MUST be boolean.
        - `overflow` in the `parity_check` MUST equal `0`.
    - If parity check is `odd`, i.e. `parity_check.r_lo == 1`:
        - `exponent` MUST reduce by 1, which means:
            - Low 128 bits of `exponent::next` MUST equal low 128 bits of `exponent::cur - 1`.
            - High 128 bits of `exponent::next` MUST equal high 128 bits of `exponent::cur`.
        - `exponent` is odd also means it was a multiplication by `base` operation, that is:
            - For each limb, `exp_table.base_limb == mul_gadget.b`.
    - If parity check if `even`, i.e. `parity_check.r_lo == 0`:
        - `exponent` MUST reduce to `exponent // 2`, which means:
            - Low 128 bits of `exponent::cur` MUST equal low 128 bits of `parity_check`'s multiplication result `d`.
                - That is, `exp_table.exponent_lo == parity_check.d_lo`.
            - High 128 bits of `exponent::cur` MUST equal high 128 bits of `parity_check`'s multiplication result `d`.
                - That is, `exp_table.exponent_hi == parity_check.d_hi`.
            - Low 128 bits of `exponent::next` MUST equal low 128 bits of `parity_check`'s multiplicand `q`.
                - That is, `exp_table.exponent_lo::next == parity_check.q_lo`. We compute `q_lo` using the 64-bit limbs of `q`.
            - High 128 bits of `exponent::next` MUST equal high 128 bits of `parity_check`'s multiplicand `q`.
                - That is, `exp_table.exponent_hi::next == parity_check.q_hi`. We compute `q_hi` using the 64-bit limbs of `q`.
        - `exponent` is even also means it was a squaring operation, that is:
            - `mul_gadget`'s multiplicands MUST be equal, or, `mul_gadget.a == mul_gadget.b`.
- For the last step, i.e. `is_last == true`, validate that `a * a == a^2 (mod 2^256)`:
    - `exponent` MUST equal `2`, that is:
        - `exp_table.exponent_lo == 2`
        - `exp_table.exponent_hi == 0`
    - Both multiplicand's of the `mul_gadget`, i.e. `a` and `b` MUST equal `base` of the exponentiation operation, that is:
        - `mul_gadget.a == base`
        - `mul_gadget.b == base` (for both these cases we equate each 64-bit limb)



## Code

Please refer to [Exponentiation Circuit Verification](`src/zkevm-specs/exp_circuit.py`).
