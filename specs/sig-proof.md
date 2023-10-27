# Signature Proof

[Elliptic Curve Digital Signature Algorithm]: https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm

According to the [Elliptic Curve Digital Signature Algorithm] (ECDSA), the signatures `(r,s)` are calculated via ECDSA from `msg_hash` and a `public_key` using the formula

`(r,s)=ecdsa(msg_hash, public_key)`

The `public_key` is obtained from `private_key` by mapping the latter to an elliptic curve (EC) point. The `r` is the x-component of an EC point, and the same EC point's y-component will be used to determine the recovery id `v = y%2` (the parity of y). Given the signature `(v, r, s)`, the `public_key` can be recovered from `(v, r, s)` and `msg_hash` using `ecrecover`.


## Circuit behavior

SigTable built inside zkevm-circuits is used to verify signatures. It has the following columns:
- `msg_hash`: Advice Column, the Keccak256 hash of the message that's signed;
- `sig_v`: Advice Column, the recovery id, either 0 or 1, it should be the parity of y;
- `sig_r`: Advice Column, the signature's `r` component;
- `sig_s`: Advice Column, the signature's `s` component;
- `recovered_addr`: Advice Column, the recovered address, i.e. the 20-bytes address that must have signed the message;
- `is_valid`: Advice Column, indicates whether or not the signature is valid or not upon signature verification.

Constraints on the shape of the table is like:

| 0 msg_hash    | 1 sig_v | 2 sig_r       | 3 sig_s       | 4 recovered_addr | 5 is_valid |
| ------------- | ------  | ------------- | ------------- | ---------------- | ---------- |
| $value{Lo,Hi} |   0/1   | $value{Lo,Hi} | $value{Lo,Hi} |   $value{Lo,Hi}  |   bool     |  


The Sig Circuit aims at proving the correctness of SigTable. This mainly includes the following type of constraints:
- Checking that the signature is obtained correctly. This is done by the ECDSA chip, and the correctness of `v` is checked separately;
- Checking that `msg_hash` is obtained correctly from Keccak hash function. This is done by lookup to Keccak table;


## Constraints

`assign_ecdsa` method takes the signature data and uses ECDSA chip to verify its correctness. The verification result `sig_is_valid` will be returned. The recovery id `v` value will be computed and verified.

`sign_data_decomposition` method takes the signature data and the return values of `assign_ecdsa`, and returns the cells for byte decomposition of the keys and messages in the form of `SignDataDecomposed`. The latter consists of the following contents:
- `SignDataDecomposed`
    - `pk_hash_cells`: byte cells for keccak256 hash of public key;
    - `msg_hash_cells`: byte cells for `msg_hash`;
    - `pk_cells`: byte cells for the EC coordinates of public key;
    - `address`: RLC of `pk_hash` last 20 bytes;
    - `is_address_zero`: check if address is zero;
    - `r_cells`, `s_cells`: byte cells for signatures `r` and `s`.

The decomposed sign data are sent to `assign_sign_verify` method to compute and verify their RLC values and perform Keccak lookup checks. 

## Code

Please refer to `src/zkevm-specs/sig_circuit.py`