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

1. If gas_left < gas_required, then is_success == false and return data is zero.
1. v, r and s are valid
  - v is 27 or 28 and the first 31 bytes of v is zero
  - both of r and s are less than `secp256k1N (0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141)`
  - both of r and s are greater than `1`
2. `sig_table` lookups
3. recovered address is zero if the signature can't be recovered.

## Code

Please refer to `src/zkevm_specs/evm_circuit/execution/precompiles/ecrecover.py`.
