# Bytecode Proof

The bytecode proof helps the EVM proof by making the bytecode (identified by its code hash) easily accessible. Each byte in the bytecode is made accessible with its position in the bytecode. It is also annotated with a flag indicating if the byte is an opcode or is simply data for a previous PUSH instruction.

## Circuit Layout

| Column                | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| `q_first`             | `1` on the first row, else `0`                                     |
| `q_last`              | `1` on the last row, else `0`                                      |
| `hash`                | The keccak hash of the bytecode                                    |
| `index`               | The position of the byte in the bytecode                           |
| `byte`                | The byte data for the current position                             |
| `is_code`             | `1` if the byte is code, `0` if the byte is PUSH data              |
| `push_data_left`      | The number of bytes that still need to follow for PUSH data        |
| `hash_rlc`            | The accumulator containg the current and previous bytes            |
| `hash_length`         | The bytecode length                                                |
| `byte_push_size`      | The number of bytes pushed for the current byte                    |
| `is_final`            | `1` if the current byte is the last byte of the bytecode, else `0` |
| `padding`             | `1` if the current row is padding, else `0`                        |
| `push_data_left_inv`  | The inverse of `push_data_left` (`IsZeroChip` helper)              |
| `push_table.byte`     | Push Table: A byte value                                           |
| `push_table.push_size`| Push Table: The number of bytes pushed for this byte as opcode     |

## Push table

The push lookup table is used to find how many bytes an opcode pushes which we need to know to detect which byte is code and which byte is not.
Because we do this lookup for each byte this table is also indirectly used to range check the byte inputs.

| Byte                                    | Num bytes pushed  |
| --------------------------------------- | ----------------- |
| \[0, OpcodeId::PUSH1\[                  | `0`               |
| \[OpcodeId::PUSH1, OpcodeId::PUSH32\]   | `[1..32]`         |
| \]OpcodeId::PUSH32, 256\[               | `0`               |

### Circuit behavior

The circuit runs over all the bytes of the bytecode starting at the byte at position `0`. Each row unrolls a single byte of the bytecode while also storing its position (`index`), the code hash it's part of (`hash`), and if it is code or not (`is_code`).

All byte data is accumulated per byte (with one byte per row) into `hash_rlc` as follows:

```
hash_rlc := hash_rlc_prev * r + byte
```

For detecting which byte is code and which byte is push data the [Push table](https://github.com/ethereum/eth2.0-specs) is used. This table allows finding out how many bytes an opcode pushes. This is used to set `push_data_left` if and only if the current byte is code (the first byte in any bytecode is code). If a row contains a non-zero value for `push_data_left` on its previous row we know the current byte is an opcode:

```
is_code := prev_push_data_left == 0
push_data_left := byte_push_size if is_code else prev_push_data_left - 1
```

At the last byte the prover can set `is_final` to `1`, which will enable the keccak lookup on `(hash_rlc, hash_length, hash)`. This will ensure that the byte data passed into the circuit matches the data the prover gave as input (all the byte data is accumulated into `hash_rlc`). This has the consequence that the circuit _requires_ the full bytecode to be a part of its state, otherwise the prover could pass in invalid byte data for the specified hash. This is enforced by the circuit by requiring the last row in the circuit (when `q_last == 1`, note that `q_first` of the next row _cannot_ be used because of unusable rows) to either have `is_final == 1` or `padding == 1`, and padding itself can only be enabled after a `is_final` was set to `1`.

## Code

Please refer to `src/zkevm-specs/bytecode.py`.
