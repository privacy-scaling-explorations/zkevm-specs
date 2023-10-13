# ecRecover precompile

## Procedure

To recover the signer from a signature. It returns signer's address if input signature is valid, otherwise returns 0.

## EVM behavior

### Inputs

The length of inputs is 128 bytes. The first 32 bytes is keccak hash of the message, and following 96 bytes are v, r, s values. v is either 27 or 28.

### Output

The recovered 20-byte address right aligned to 32 byte. If an address can't be recovered or not enough gas was given, then return 0.

### Gas cost

A constant gas cost: 3000

## Constraints

1. v is 27 or 28.
2. `sig_table` lookups
3. recovered address is zero if the signature can't be recovered.

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ecrecover.py`.
