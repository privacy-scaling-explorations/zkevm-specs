# Ecc Proof

EccCircuit supports three ECC operations which are addition, multiplication and pairing. This circuit provides the correctness of `EccTable`.

## Circuit behavior

EccTable built inside zkevm-circuits is used to verify ECC operations. It has the following columns:
- `op_type`: Types of ecc operations, `Add`, `Mul` and `Pairing`
- `px`: x-coordinate of point 1
- `py`: y-coordinate of point 1
- `qx`: scalar number if `op_type` is `Mul` otherwise it's x-coordinate of point 2 
- `qy`: zero if `op_type` is `Mul` otherwise it's y-coordinate of point 2
- `outx`: x-coordinate of output
- `outy`: y-coordinate of output
- `is_valid`: Indicates whether the operation is valid or not.

Constraints on the shape of the table is like:

| 0 op_type | 1 px          | 2 py          | 3 qx          | 2 qy          | 2 outx        | 2 outy        | 4 is_valid |
| --------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ---------- |
|   $tag    | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} |    bool    |  

- tag: `Add`, `Mul` and `Pairing`


## Constraints

This mainly includes the following type of constraints:
- Checking `op_type` is one of `Add`, `Mul` or `Pairing`.
- Checking p and q are valid curve points.
- Checking the correctness amon p, q and out. This is done by `ECCVerifyChip`.


## Code

Please refer to `src/zkevm-specs/ecc_circuit.py`