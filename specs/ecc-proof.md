# Ecc Proof

EccCircuit supports three ECC operations and those are addition, multiplication and pairing. This circuit provides the correctness of `EccTable`.

## Circuit behavior

EccTable built inside zkevm-circuits is used to verify ECC operations. It has the following columns:
- `op_type`: Types of ecc operations, `Add`, `Mul` and `Pairing`
- `px`: x-coordinate of point 1 if `op_type` is `Mul` or `Add` otherwise it's zero
- `py`: y-coordinate of point 1 if `op_type` is `Mul` or `Add` otherwise it's zero
- `qx`: x-coordinate of point 2 if `op_type` is `Add`. Scalar number if `op_type` is `Mul` otherwise it's zero
- `qy`: y-coordinate of point 2 if `op_type` is `Add` otherwise it's zero
- `input_rlc`: rlc of input data if `op_type` is `Pairing` otherwise it's zero
- `outx`: x-coordinate of output if `op_type` is `Mul` or `Add` otherwise it's zero
- `outy`: y-coordinate of output if `op_type` is `Mul` or `Add` otherwise it indicates pairing operation being successful or not
- `is_valid`: Indicates whether the operation is valid or not.

`Pairing` allows multiple input points, and `p` and `q` are not enough to represent multiple points so we introduce `input_rlc` to represent all the input points. Therefore, `input_rlc` is a non-zero value only when `op_type` is `Pairing` otherwise it should be zero.

Constraints on the shape of the table is like:

| 0 op_type | 1 px          | 2 py          | 3 qx          | 4 qy          | 5 input_rlc   | 6 outx        | 7 outy        | 8 is_valid |
| --------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ------------- | ---------- |
|   $tag    | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $input_rlc    | $value{Lo,Hi} | $value{Lo,Hi} |    bool    |  
|...||||||||
|   ADD    | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | 0   | $value{Lo,Hi} | $value{Lo,Hi} |    0/1    |  
|   MUL    | $value{Lo,Hi} | $value{Lo,Hi} | $value{Lo,Hi} | 0 | 0   | $value{Lo,Hi} | $value{Lo,Hi} |    0/1    |  
|  PAIRING | 0 | 0 | 0 | 0 | $value:rlc   | 0 | 0/1 |    0/1    |  

- tag: `Add`, `Mul` and `Pairing`


## Constraints

This mainly includes the following type of constraints:
- Checking `op_type` is one of `Add`, `Mul` or `Pairing`.
- Checking p and q are valid points if `op_type` is `Add` or `Mul`, and `input_rlc` is zero. A valid point means
  - it's less than bn128.`FQ (30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD47)`.
  - it's on the curve.
- Checking `input_rlc` is valid if `op_type` is `Pairing`, and p, q and outx are zero.
- Checking the correctness among p, q and out. This is done by `ECCVerifyChip`.


## Code

Please refer to `src/zkevm-specs/ecc_circuit.py`