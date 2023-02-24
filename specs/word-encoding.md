# Word Encoding

In the EVM every word is 256 bits. But in the zkevm, we need to break the word in 8 bit chunks due to two limitations.

1. We use the BN254 curve. The largest number the BN254 curve can represent is 254 bits. All arithmetic is done modulo a 254 bit prime.
2. We perform conditional checks and bitwise operations with plookups. The 2^25 row size limits us to work those in smaller chunks of the word. With plookup we have to do polynomial divisions. Plonk prover uses FFT to efficiently perform polynomial divisions. The BN254 curve allows for FFTs or size 2^28. Some of which are required for constant overhead and custom constraints. So we try and limit all our polynomial degrees at 2^25.

In this document, we define the commitment of the 256 bit word, and the operation on them in the circuit.

## Endianness

We encode the 256 bit word in little endian.

For example, a 256 bit value 1

```python
word256 = 1
```

`word256` can be broken down into 32 8 bit words.

```python
word8s = [
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
]
```

## Commitment

The 256 bit word is represented as a random linear combination of its 8 bit words.

The commitment check should gurantee the 32 chunks in 8 bit range.

## Addition

This checks the validity of `a256 + b256 = c256`

The overflow is supported to match the EVM behavior.

Example:

```
a8s    ff 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0
b8s     2 1 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0
carry     1 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 0
sum8s   1 2 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0
```

```
a8s    ff ff ff ff ff ff ff ff | ff ff ff ff ff ff ff ff | ff ff ff ff ff ff ff ff | ff ff ff ff ff ff ff ff
b8s     2  0  0  0  0  0  0  0 |  0  0  0  0  0  0  0  0 |  0  0  0  0  0  0  0  0 |  0  0  0  0  0  0  0  0
carry      1  1  1  1  1  1  1 |  1  1  1  1  1  1  1  1 |  1  1  1  1  1  1  1  1 |  1  1  1  1  1  1  1  1  1
sum8s   1  0  0  0  0  0  0  0 |  0  0  0  0  0  0  0  0 |  0  0  0  0  0  0  0  0 |  0  0  0  0  0  0  0  0
```

## Comparator

This checks the the relations of `a256 > b256`, `a256 < b256`, `a256 == b256`

We group 8 bit chunks to 16 bit chunks to optimize the table.

The `result` carries the conclusion of the comparision from the higher siganificant chunks all the way down.

Example:

```
a       1 0 0 0 | 0 0 0 0 | 0 0 0 0 | 0 1 0 0 |
b       1 0 0 0 | 0 0 0 0 | 0 0 0 0 | 0 0 0 0 |
result  1 1 1 1 | 1 1 1 1 | 1 1 1 1 | 1 1 0 0 |
```
