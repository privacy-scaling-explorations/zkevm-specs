# dataCopy precompile

## Procedure

The `dataCopy` precompile returns its input.

### Circuit behavior

1. Do a busmapping lookup for CallContext CalleeAddress.
2. Do a busmapping lookup for CallContext CallerId.
3. Do a busmapping lookup for CallContext CallDataOffset.
4. Do a busmapping lookup for CallContext CallDataLength.
5. Do a busmapping lookup for CallContext ReturnDataOffset.
6. Do a busmapping lookup for CallContext ReturnDataLength.
7. Do a CopyTable lookup to verify the copy from calldata to current call context memory.
8. Do a CopyTable lookup to verify the copy from calldata to precompile call context memory.

### Gas cost

The gas cost of `dataCopy` precompile consists of two parts:

1. A constant gas cost: `15 gas`
2. A dynamic gas cost: cost of copying (variable depending on the `size` copied to memory)

## Constraints

1. prId == 0x04
2. state transition:
   - rw_counter + 5 + 2 * `copy_length`
   - gas + 15 + dynamic cost (copier cost)

## Code

Please refer to `src/zkevm_specs/contract/dataCopy.py`.
