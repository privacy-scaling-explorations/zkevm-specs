# ecMul precompile

## Procedure

The `ecMul` precompile calculates scalar multiplication on a given point and return result point over alt_bn128 curve. 

### Circuit behavior

The inputs include two parts, the first 64 bytes is the point, and the following 32 bytes is the scalar used for the multiplication.

```
input[0; 31] (32 bytes): x
input[32; 63] (32 bytes): y
input[64; 95] (32 bytes): s
```

The multiplication result is returned and the size is `64` bytes.

```
input[0; 31] (32 bytes): x
input[32; 63] (32 bytes): y
```

### Gas cost

A constant gas cost: 6000

If the input is not valid, all gas provided is consumed.

## Constraints

1. `ecc_table` lookup
2. If `s` is zero or `p` is an infinite point
  - output is zero
3. If `is_valid` is false,
  - output is zero
  - consume all the remaining gas

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ec_mul.py`.
