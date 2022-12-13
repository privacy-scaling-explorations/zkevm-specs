# Bytecode Proof

The bytecode proof helps the EVM proof by making the bytecode (identified by its code hash) easily accessible. Each byte in the bytecode is made accessible with its position in the bytecode. It is also annotated with a flag indicating if the byte is an opcode or simply data for a previous PUSH instruction.

## Circuit Layout

The collumn `tag` (advice) makes the circuit behave as a state machine, selecting different constrains depending on the current and next row value. The `tag` collumn can have two different values: Header, Byte. A row of `tag==Header` preceeds a series of `tag==Byte` rows that contain a complete bytecode sequence. The row `tag==Header` contains the length of the bytecode and the hash of the bytecode, each `tag==Byte` contains one byte of the bytecode, bytecode hash, its lenght and other for the push data.


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
| `length`              | The bytecode length, that could be 0 for empty byrecodes and padding|
| `push_data_size`      | The number of bytes pushed for the current byte                     |
| `push_table.byte`     | Push Table: A byte value                                            |
| `push_table.push_size`| Push Table: The number of bytes pushed for this byte as opcode      |


After all the bytecodes have been added, the rest of the rows are filled with padding in the form of `tag == Header && length == 0 && value ==0` rows.

Additionally we will need two collumns for IsZeroChip for `length` and `push_data_left`


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

next.value_rlc := curr.value_rlc * r + next.value
```

For detecting which byte is code and which byte is push data the [Push table](#push-table) is used. This table allows finding out how many bytes an opcode pushes. This is used to set `push_data_left` (`push_data_size + 1`) if and only if the current byte is code (the first byte in any bytecode is code).

If a row contains a non-zero value for `push_data_left` on its previous row we know the current byte is an opcode:

```
first_bytecode.is_code := 1
curr.is_code := curr.push_data_left == 0
next.push_data_left := curr.byte_push_size if curr.is_code else curr.push_data_left - 1
```

The fixed columns `q_first` and `q_last` should be zero for all rows, except the first one where `q_first := 1` and the last one where `q_last:=1`.

## Circuit constrains

All circuit constrains are based on the current row (`curr`) and the `next` row.

First of all if `curr.q_first` or `curr.q_last` are `1`, then `curr.tag == Header`.

We should have the following contrains based on `curr.tag` and `next.tag` (state transition), for all rows except the last one (`curr.q_last == 1`).

To enable lookup all `curr.tag == Header` rows should have:

```
assert curr.index == 0
assert curr.value == curr.length
```

Also, each `curr.tag == Byte` should have:

```
assert push_data_size_table_lookup(curr.value, curr.push_data_size)
assert curr.is_code == (curr.push_data_left == 0)
if curr.is_code:
    assert next.push_data_left == curr.push_data_size
else:
    assert next.push_data_left == curr.push_data_left - 1
```

This way we make sure is_code and next.push_data_left has the right values.

### curr.tag == Header and next.tag == Header

We are in a transition from a empty bytecode to the begining of another bytecode that could be empty or not.

Hence:
```
assert curr.length == 0
assert curr.hash == EMPTY_HASH
```

### curr.tag == Header and next.tag == Byte

We are at the begining of a non-empty bytecode.

Hence:

```
assert next.length == curr.length
assert next.index == 0
assert next.is_code == 1
assert next.hash == curr.hash
assert next.value_rlc == next.value
```

### curr.tag == Bytecode and next.tag == Byte

We are working on an actual bytecode byte that is not the last one.

Hence:

```
assert next.length == curr.length
assert next.index == curr.index + 1
assert next.hash == curr.hash
assert next.value_rlc == curr.value_rlc * randomness + next.value
```

We make sure that `index` is incremented and `value_rlc` is accumulated.

### curr.tag == Bytecode and next.tag == Header

We are at the last byte of a bytecode.

Hence:

```
assert curr.index + 1 == curr.length
assert keccak256_table_lookup(curr.hash, curr.length, curr.value_rlc)
```

First, we make sure that the bytecode has `curr.length` bytes in the table.

Second, we ensure that the byte data passed into the circuit matches the data the prover gave as input (all the byte data is accumulated into `value_rlc`). This has the consequence that the circuit _requires_ the full bytecode to be a part of its state, otherwise the prover could pass in invalid byte data for the specified hash.


## Code

Please refer to `src/zkevm-specs/bytecode.py`.
