# ecPairing precompile

## Procedure

The `ecPairing` precompile computes the bilinear map between two given points in the groups G1 and G2, respectively, over the alt_bn128 curve.

### Circuit behavior

The inputs is a multiple of 6 32-byte values. One set of inputs is defined as follows

```
input[0; 31] (32 bytes): x1
input[32; 63] (32 bytes): y1
input[64; 95] (32 bytes): x2
input[96; 127] (32 bytes): y2
input[128; 159] (32 bytes): x3 (result)
input[160; 192] (32 bytes): y3 (result)
```

The output is the result of `ecPairing`, 1 if the pairing is successful, 0 otherwise.

```
input[0; 31] (32 bytes): success
```

### Gas cost

1. A constant gas cost: 45,000
2. A dynamic gas cost: 34,000 * (len(data) / 192)

If the input is not valid, all gas provided is consumed.

## Constraints

1. The length of inputs must be a multiple of 192 bytes.
1. `ecc_table` lookup
2. If `is_valid` is false,
  - output is zero
  - consume all the remaining gas

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ec_pairing.py`.
