# bn256 Proof

The bn256 proof checks values in bn256 table and applies the lookup arguments to the corresponding tables to check if bn256 operation is correct.

## Circuit Layout

The bn256 circuit contains columns from the [bn256 table](./tables.md#exponentiation-table#bn256-table) with the same witness assignment and additionally consists of the following columns.

1. `bn256_table`: The columns from [bn256 table](./tables.md#exponentiation-table#bn256-table).
2. `bn256_gadget`: The columns from a bn256 point arithmetics gadget for validating that each step within the bn256 arthmetic trace was calculated correctly.

## Circuit Constraints

- For every row where `is_step == true`, except the last step, validate that:
    - `id`, `tag` and `input_length` MUST be the same across subsequent steps.
    - `value_alt` MUST be 0

- For every row, validate that:
    - `is_step` and `is_last` MUST be boolean.
    - `tag` MUST be in from 0 to 3.
    - `input_length` MUST match number corresponding `tag`.
        - `ecRecover`: 0
        - `ecAdd`: 1
        - `ecMul`: 2
        - `ecPairing`: more than 3

- For every row where `is_step == true`, validate that:
    - `value` MUST equal `bn256_gadget` result.

- For the last step where `is_last == true`, validate that:
    - `value` MUST match the type corresponding `tag`.
        - `ecRecover`: address
        - `ecAdd`: 32 bytes
        - `ecMul`: 32 bytes
        - `ecPairing`: boolean
    - `value_alt` MUST match the type corresponding `tag`.
        - `ecRecover`: 0
        - `ecAdd`: 32 bytes
        - `ecMul`: 32 bytes
        - `ecPairing`: 0

## Code

Please refer to `src/zkevm-specs/bn256_circuit.py`
