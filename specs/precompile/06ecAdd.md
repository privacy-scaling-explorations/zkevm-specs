# ecAdd precompile

Point addition (ADD) on the elliptic curve 'alt_bn128'. The point at infinity is encoded with both field x and y at 0.

## EVM behavior

#### Inputs

The length of inputs is 128 bytes. The first 64 bytes is x coordinate and y coordinate of the first point. The second 64 bytes is x coordinate and y coordinate of the second point. Each coordinate (x or y) is a 32 bytes data.

#### Output

The length of output is 64 bytes. It's the addition result of two input points.

#### Gas cost

A constant gas cost: 150

If the input is not valid, all gas provided is consumed.

## Constraints

1. `ecc_table` lookup
2. If `is_valid` is false,
  - output is zero
  - consume all the remaining gas

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ec_add.py`.
