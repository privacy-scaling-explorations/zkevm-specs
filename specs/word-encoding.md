# Word Encoding

In the EVM every word is 256 bits. But in the zkevm due to two limitations we need to break the word in 8 bit chunks.

- We are using a BN254 curves so the artithmatics in the circuit is less than 256 bits.
- Some operations require a plookup table lookup, which constraints the how large the number we can operate at a time.

In this document we defines the commitment of the 256 bit word, and the operation on them in the circuit.

## Endianness

We encode the 256 bit word in little endian.

For example, a 256 bit value 1

```python
word256 = 1
```
`word256` can be broken down into 32 8 bit words.

```python
word8s = [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```

See `src/encoding/utils.py::u256_to_u8s` and `src/encoding/utils.py::u8s_to_u256` for the functions to convert between a 256 bit word and its 8 bit chunks.

## Commitment

The 256 bit word is represented as a random linear combination of its 8 bit words.

The commitment check should gurantee the 32 chunks in 8 bit range.

See `src/encoding/commitment.py::check_commitment`

## Addition

This checks the validity of `a256 + b256 = c256`

See `src/encoding/addition.py::check_add`

## Comparator

This checks the the relations of `a256 > b256`, `a256 < b256`, `a256 == b256`

See `src/encoding/comparator.py::compare`
