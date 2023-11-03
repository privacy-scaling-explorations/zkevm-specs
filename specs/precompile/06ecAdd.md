# ecAdd precompile

## Procedure

The `ecAdd` precompile add two given points and return result point over alt_bn128 curve. Firstly, the input is divided into four parts to get two points $x$ and $y$. Secondly, the alt_bn128 points are initialized with given pairs of $x$ and $y$. Finally, the result point is returned.

### Circuit behavior

Two points are recovered from input. The field is expressed as `32` bytes for each and the input includes two points so the input size is `128` bytes.

```
input[0; 31] (32 bytes): x1
input[32; 63] (32 bytes): y1
input[64; 95] (32 bytes): x2
input[96; 128] (32 bytes): y2
```

These two points are added and the result is returned. The result size is `64` bytes and $x$ and $y$ are montgomery form.

```
input[0; 31] (32 bytes): x
input[32; 63] (32 bytes): y
```

### Gas cost

A constant gas cost: 150

If the input is not valid, all gas provided is consumed.

## Constraints

1. `ecc_table` lookup
2. If `is_valid` is false,
  - output is zero
  - consume all the remaining gas

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ec_add.py`.
