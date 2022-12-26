# Bytecode Proof

The bytecode proof helps the EVM proof by making the bytecode (identified by its code hash) easily accessible. Each byte in the bytecode is made accessible with its position in the bytecode. It is also annotated with a flag indicating if the byte is an opcode or simply data for a previous PUSH instruction.

## Circuit Layout

The column `tag` (advice) makes the circuit behave as a state machine, selecting different constraints depending on the current and next row value. The `tag` column can have two different values: Header, Byte. A row of `tag==Header` precedes a series of `tag==Byte` rows that contain a complete bytecode sequence. The row `tag==Header` contains the length of the bytecode and the hash of the bytecode, each `tag==Byte` contains one byte of the bytecode, bytecode hash, its length and other for the push data.


| Column                | Description                                                         |
| --------------------- | --------------------------------------------------------------------|
| `q_first` (fixed)     | `1` on the first row, else `0`                                      |
| `q_last` (fixed)      | `1` on the last row, else `0`                                       |
| `hash`                | The keccak hash of the bytecode                                     |
| `index`               | The position of the byte in the bytecode starting from 0            |
| `value`               | Value for this row bytecode byte, and the length in Header rows.    |
| `is_code`             | `1` if the byte is code, `0` if the byte is PUSH data               |
| `push_data_left`      | The number of PUSH data bytes that still follow the current row     |
| `value_rlc`           | The accumulator containing the current and previous bytes RLC       |
| `length`              | The bytecode length, that could be 0 for empty bytecodes and padding|
| `push_data_size`      | The number of bytes pushed for the current byte                     |
| `push_table.byte`     | Push Table: A byte value                                            |
| `push_table.push_size`| Push Table: The number of bytes pushed for this byte as opcode      |


After all the bytecodes have been added, the rest of the rows are filled with padding in the form of `tag == Header && length == 0 && value == 0 && hash == EMPTY_HASH` rows.

Additionally we will need two columns for IsZeroChip for `length` and `push_data_left`


## Push table

The push lookup table is used to find how many bytes an opcode pushes, which we need to know to detect which byte is code and which byte is not.

Because we do this lookup for each byte, this table is also indirectly used to range check the byte inputs.

| Byte                                    | Num bytes pushed  |
| --------------------------------------- | ----------------- |
| \[0, OpcodeId::PUSH1\]                  | `0`               |
| \[OpcodeId::PUSH1, OpcodeId::PUSH32\]   | `[1..32]`         |
| \[OpcodeId::PUSH32, 256\]               | `0`               |

## Witness generation

The circuit starts by adding a row that contains the bytecode length using `tag = Header`.

Then it runs over all the bytes of the bytecode in order starting at the byte at position `0`.
Each following row unrolls a single byte (using `tag = Byte` and `value = the actual byte value`) of the bytecode while also storing its position
(`index`), the code hash it's part of (`hash`), and if it is code or not
(`is_code`). Also `push_data_size` is filled to match the push table, and `push_data_left` is computed.

All byte data is accumulated per byte (with one byte per row) into `value_rlc` as follows, where r is a challenge:

```
first_bytecode.value_rlc := firstbytecode.value

next.value_rlc := cur.value_rlc * r + next.value
```

For detecting which byte is code and which byte is push data the [Push table](#push-table) is used. This table allows finding out how many bytes an opcode pushes. This is used to set `next.push_data_left` if and only if the current byte is code (the first byte in any bytecode is code).

If a row contains a zero value for `push_data_left` we know the current byte is an opcode:

```
first_bytecode.is_code := 1
cur.is_code := cur.push_data_left == 0
next.push_data_left := cur.byte_push_size if cur.is_code else cur.push_data_left - 1
```

The fixed columns `q_first` and `q_last` should be zero for all rows, except the first one where `q_first := 1` and the last one where `q_last := 1`.

## Circuit constrains

All circuit constraints are based on the current row (`cur`) and the `next` row.

First of all if `cur.q_first` or `cur.q_last` are `1`, then `cur.tag == Header`.

We should have the following constraint based on `cur.tag` and `next.tag` (state transition), for all rows except the last one (`cur.q_last == 1`).

To enable lookup all `cur.tag == Header` rows should have:

```
assert cur.index == 0
assert cur.value == cur.length
```

Also, each `cur.tag == Byte` should have:

```
assert push_data_size_table_lookup(cur.value, cur.push_data_size)
assert cur.is_code == (cur.push_data_left == 0)
if cur.is_code:
    assert next.push_data_left == cur.push_data_size
else:
    assert next.push_data_left == cur.push_data_left - 1
```

This way we make sure is_code and next.push_data_left has the right values.

### cur.tag == Header and next.tag == Header

We are in a transition from a empty bytecode to the begining of another bytecode that could be empty or not.

Hence:
```
assert cur.length == 0
assert cur.hash == EMPTY_HASH
```

### cur.tag == Header and next.tag == Byte

We are at the begining of a non-empty bytecode.

Hence:

```
assert next.length == cur.length
assert next.index == 0
assert next.is_code == 1
assert next.hash == cur.hash
assert next.value_rlc == next.value
```

### cur.tag == Byte and next.tag == Byte

We are working on an actual bytecode byte that is not the last one.

Hence:

```
assert next.length == cur.length
assert next.index == cur.index + 1
assert next.hash == cur.hash
assert next.value_rlc == cur.value_rlc * randomness + next.value
```

We make sure that `index` is incremented and `value_rlc` is accumulated.

### cur.tag == Bytecode and next.tag == Header

We are at the last byte of a bytecode.

Hence:

```
assert cur.index + 1 == cur.length
assert keccak256_table_lookup(cur.hash, cur.length, cur.value_rlc)
```

First, we make sure that the bytecode has `cur.length` bytes in the table.

Second, we ensure that the byte data passed into the circuit matches the data the prover gave as input (all the byte data is accumulated into `value_rlc`). This has the consequence that the circuit _requires_ the full bytecode to be a part of its state, otherwise the prover could pass in invalid byte data for the specified hash.


## Code

Please refer to `src/zkevm-specs/bytecode.py`.
