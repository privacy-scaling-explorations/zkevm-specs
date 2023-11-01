# Ecc Proof

EccCircuit supports three ECC operations which are addition, multiplication and pairing. This circuit provides the correctness of `EccTable`.

## Circuit behavior

EccTable built inside zkevm-circuits is used to verify ECC operations. It has the following columns:
- `op_type`: Types of ecc operations, `Add`, `Mul` and `Pairing`
- `px`: x-coordinate of point 1 if `op_type` is `Mul` or `Add` otherwise it's zero
- `py`: y-coordinate of point 1 if `op_type` is `Mul` or `Add` otherwise it's zero
- `qx`: x-coordinate of point 2 if `op_type` is `Add`. Scalar number if `op_type` is `Mul` otherwise it's zero
- `qy`: y-coordinate of point 2 if `op_type` is `Add` otherwise it's zero
- `input_rlc`: rlc of input data if `op_type` is `Pairing` otherwise it's zero
- `outx`: x-coordinate of output
- `outy`: y-coordinate of output
- `is_valid`: Indicates whether the operation is valid or not.

`Pairing` allows multiple input points, and `p` and `q` are not enough to represent multiple points so we introduce `input_rlc` to represent all the input points. Therefore, `input_rlc` is a non-zero value only when `op_type` is `Pairing` otherwise it should be zero.

Constraints on the shape of the table is like:

| 0 op_type | 1 px          | 2 py          | 3 qx          | 4 qy          | 5 input_rlc   | 6 outx        | 7 outy        | 8 is_valid |
| --------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ---------- |
|   $tag    | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $input_rlc    | $value{Lo,Hi} | $value{Lo,Hi} |    bool    |  

- tag: `Add`, `Mul` and `Pairing`


## Constraints

This mainly includes the following type of constraints:
- Checking `op_type` is one of `Add`, `Mul` or `Pairing`.
- Checking p and q are valid curve points if `op_type` is `Add` or `Mul`, and `input_rlc` is zero.
- Checking `input_rlc` is valid if `op_type` is `Pairing`, and p and q are zero.
- Checking the correctness among p, q and out. This is done by `ECCVerifyChip`.


## Code

Please refer to `src/zkevm-specs/ecc_circuit.py`