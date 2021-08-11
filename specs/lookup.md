# Plookup Table

We use the [halo2 lookup table](https://zcash.github.io/halo2/design/proving-system/lookup.html) as a primitive to check if some adviced values are a row of a table.

Example:

This table has columns "a", "b", and "c". Where "a" and "b" are possible combinations of 0, 1, 2. "c" is the logic AND operations on "a" and "b".

| a   | b   | c   |
| --- | --- | --- |
| 0   | 0   | 0   |
| 0   | 1   | 0   |
| 0   | 2   | 0   |
| 1   | 0   | 0   |
| 1   | 1   | 1   |
| 1   | 2   | 0   |
| 2   | 0   | 0   |
| 2   | 1   | 0   |
| 2   | 2   | 2   |

We can use the table to check the AND operation constraints on some variable x and y in the circuit by proving "x", "y", and "x & y" are cells of a row in the table.

## Fixed Table

Rows of a fixed table are determined "before" proving time.

The AND operation table is an example.

## Variable Table

Rows of a variable table are determined "at" proving time.

It allows prover to create their own table. An example would be the prover can witness a key-value mapping as a variable table. Note that we need extra check to gurantee the uniqueness of the mapping key.