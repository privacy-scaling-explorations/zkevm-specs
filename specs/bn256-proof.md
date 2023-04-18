# bn256 Proof

The bn256 proof checks values in bn256 table and applies the lookup arguments to the corresponding tables to check if bn256 operation is correct.

## Circuit Layout

The bn256 circuit contains columns from the [bn256 table](./tables.md#exponentiation-table#bn256-table) with the same witness assignment and additionally consists of the following columns.

1. `bn256_table`: The columns from [bn256 table](./tables.md#exponentiation-table#bn256-table).
2. `bn256_gadget`: The columns from a bn256 point arithmetics gadget for validating that each step within the bn256 arthmetic trace was calculated correctly.

## Circuit Constraints

bn256 table has a single row and it's constrained by bn256 gadget.
bn256 field is represented as 32 bytes and bn256 points are 64 bytes.

- For every operation, validate that:
    - `tag` MUST be in from 0 to 3.
    - `input0` MUST match the type corresponding `tag`.
        - `ecRecover`: 32 bytes
        - `ecAdd`: bn256 field
        - `ecMul`: bn256 field
        - `ecPairing`: bn256 field
    - `input1` MUST match the type corresponding `tag`.
        - `ecRecover`: bn256 field
        - `ecAdd`: bn256 field
        - `ecMul`: bn256 field
        - `ecPairing`: bn256 field
    - `input2` MUST match the type corresponding `tag`.
        - `ecRecover`: bn256 field
        - `ecAdd`: bn256 field
        - `ecMul`: 0
        - `ecPairing`: bn256 field
    - `input3` MUST match the type corresponding `tag`.
        - `ecRecover`: bn256 field
        - `ecAdd`: bn256 field
        - `ecMul`: bn256 field
        - `ecPairing`: bn256 field
    - `output0` MUST match the type corresponding `tag`.
        - `ecRecover`: 32 bytes
        - `ecAdd`: bn256 field
        - `ecMul`: bn256 field
        - `ecPairing`: boolean
    - `output1` MUST match the type corresponding `tag`.
        - `ecRecover`: 0
        - `ecAdd`: bn256 field
        - `ecMul`: bn256 field
        - `ecPairing`: 0

For each operation, bn256 gadget validates the relation between input and output.

## Code

Please refer to `src/zkevm-specs/bn256_circuit.py`
