# ecPairing precompile

## Procedure

The `ecPairing` precompile computes the bilinear map between two given points in the groups G1 and G2, respectively, over the alt_bn128 curve.

### Circuit behavior

The input is arbitrarily many pairs of elliptic curve points. Each pair is given as a six 32-bytes values and is constructed as follows

```
input[0; 31] (32 bytes): x1
input[32; 63] (32 bytes): y1
input[64; 95] (32 bytes): x2
input[96; 127] (32 bytes): y2
input[128; 159] (32 bytes): x3 (result)
input[160; 191] (32 bytes): y3 (result)
```

The first two 32-bytes values represent the first point (px, py) from group G1, the next four 32-bytes values represent the other point (qx, qy) from group G2.

The bn254Pairing code first checks that a multiple of 6 elements have been sent, and then performs the pairings check(s). The check that is performed for two pairs is e(p1, q1) = e(-p2, q2) which is equivalent to the check e(p1, q1) * e(p2, q2) = 1.

The output is 1 if all pairing checks were successful, otherwise it returns 0.

```
input[0; 31] (32 bytes): success
```

The pairing checks fail if not having a multiple of 6 32-bytes values or in the case of the points not being on the curve. In these cases all the provided gas is consumed. For these cases, the variable is_valid is set to 0. The variable output denotes whether the pairing checks were successful (in the case of is_valid = 1)
### Gas cost

1. A constant gas cost: 45,000
2. A dynamic gas cost: 34,000 * (len(data) / 192)

If the input is not valid, all gas provided is consumed.

## Constraints

1. If the length of the input is not a multiple of 192 bytes
  - output is 0
2. If the input is empty which means it's a successful call,
  - `input_rlc` is zero
  - output is 1
3. `ecc_table` lookup
4. If `is_valid` is false,
  - output is 0
  - consume all the remaining gas

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ec_pairing.py`.
