# dataCopy precompile

## Procedure

The `dataCopy` precompile returns its input.

The gas cost of `dataCopy` precompile consists of two parts:

1. A constant gas cost: `15 gas`
2. A dynamic gas cost: cost of copying (variable depending on the `size` copied to memory)

## Constraints

1. prId = PrecompileId(0x04)
2. state transition:
   - gas + 15 + dynamic cost (copier cost)

## Code

Please refer to `src/zkevm_specs/native/execution/dataCopy.py`.
