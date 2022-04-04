# Keccak256 For Variable Length Input

We describe the circuit that can process inputs of an arbitrary size.

## Plain Keccak behavior

Keccak256 uses a simple iterating sponge construction to handle a variable length input. The sponge absorbs 17 words(136 bytes) of inputs, applies the `Keccak-f` permutation, and then absorb next 17 words. Once all parts of the inputs are absorbed, the sponge squeezes out the 32 bytes for the output.

No matter what input is, the padding must be applied. The padding is a multi-rate padding, it pads single bit 1 followed by minimum number of bits 0 followed by a single bit 1, such that the result is 136 bytes.

## Circuit behavior

### Gadget: Keccak Output Lookup

Each row other than the first is corresponding to a `Keccak-f` permutation round.

We define these state tags
- Absorb: Absorbs the current input and permutes state.
- Finalize: Does the same but it marks the state output is usable for the consumer.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Absorb
    Absorb --> Absorb
    Absorb --> Finalize
    Finalize --> Absorb
    Finalize --> Finalize
    Finalize --> [*]
```

#### State transition


We leave an empty row at the top of the table for usage that disables the lookup. Use a separate selector `q_start` for this row.

This region splits the input to multiple parts, each part corresponds to their `Keccak-f` permutation round.
This is also a lookup table for the other circuits to lookup the Keccak256 input to the output.

Columns:

- `state_tag` either 0=Start/End/Null, 1=Absorb, 2=Finalize
- `input_len` The length of the input.
- `input` 136 bytes to be absorbed in this round. Padding not included yet.
- `perm_count` Permutations we have done after the current one.
- `acc_input` Accumulatd bytes by random linear combination (in big-endian order)
- `output` The base-2 `state[:4]` output from this round `keccak_f`

| state_tag | input_len | input | perm_count | acc_input | output |
| --------: | --------: | ----: | ---------: | --------: | -----: |
|         0 |         0 |     0 |          0 |         0 |      0 |
|  Finalize |        20 |       |          1 |           |        |
|    Absorb |       150 |       |          1 |           |        |
|  Finalize |       150 |       |          2 |           |        |
|  Finalize |         0 |       |          1 |           |        |
|    Absorb |       136 |       |          1 |           |        |
|  Finalize |       136 |     0 |          2 |           |        |
|         0 |           |       |          0 |         0 |        |

#### Checks

We branch the constraints to apply by state_tag

- `q_start`
  - State transition
    - next.state_tag in (Absorb, Finalize)
- Absorb
  - if input_len === 136 * (perm_count + 1) absorb a full block of 0x80...0x01
    - next.input === 0 (since the input is the unpadded input)
    - next.state_tag in (Absorb, Finalize)
  - Next row validity
    - next.acc_input === curr.acc_input * r**136
    - next.perm_count === next.perm_count + 1
  - State transition
    - next.state_tag in (Absorb, Finalize)
- Finalize
    - This is a valid place to finalize
        - (curr.perm_count * 136 - input_len) in 1~136
    - Next row validity
        - next.perm_count === 1
    - State transition: (Absorb, Finalize, 0) all 3 states allowed
- 0
    - next.state_tag === 0 (The first row is also satisfied!)
    - We can broadcast this state_tag to the `keccak_f` as a flag to disable all checks.


#### Lookup

To lookup the Keccak256 input to the output, query the following columns:

- `state_tag`
- `input_len`: FQ. This is required because input \[0, 0, 0\] and \[0, 0\] have the same RLC value but different keccak hash outputs.
- `acc_input`: RLC
- `output`: RLC

When the lookup is needed, constrain `state_tag === 2 (Finalize)`.

### Gadget: Padding Validator

When the state_tag is Finalize, we activate this region to check the padded input.

#### Plain behavior: The padding rule

```python
def get_padding(input_len: int, perm_count: int) -> bytes:
    """
    output big-endian bytes
    """
    acc_len = (perm_count - 1) * 136
    # note that diff is at maximum 135
    diff = input_len - acc_len
    if diff == 0:
        # pad the next full block
        return [0x80] + ([0x00] * 134) + [0x01]
    elif diff == 1:
        # pad 0b10000001
        return [0x81]
    elif 1 < diff < 136:
        return [0x80] + ([0x00] * int(diff - 2)) + [0x01]
    else:
        raise ValueError("unreachable")
```

#### Circuit

The Padding Region is a 136-row region.

- `byte` individual byte of the input in big-endian
- `input_len` Length for correct padding
- `acc_len` How many bytes we have processed
- `condition_80_inv` The inverse of `input_len - acc_len` or 0.
- `padded_byte` Mostly the same as the original `byte` but padded
- `is_pad_zone` A flag to define the rows that `byte` should be 0
- `byte_RLC` This accumulate `byte` into RLC

| offset | byte | input_len | acc_len | condition_80_inv | padded_byte | is_pad_zone | byte_RLC |
| -----: | :--- | --------: | ------: | ---------------: | :---------- | ----------: | -------- |
|      0 | 0    |       250 |     2   |                  | 0           |           0 |          |
|      1 | 0xff |       250 |     136 |                  | 0xff        |           0 |          |
|      2 | 0xff |       250 |     137 |                  | 0xff        |           0 |          |
|    ... |  ... |       ... |     ... |                  | ...         |           0 |          |
|    114 | 0xff |       250 |     249 |                1 | 0xff        |           0 |          |
|    115 | 0x00 |       250 |     250 |                0 | 0x80        |           1 |          |
|    116 | 0x00 |       250 |     251 |               -1 | 0x00        |           1 |          |
|    ... | ...  |       ... |     ... |              ... | ...         |         ... |          |
|    135 | 0x00 |       250 |     270 |                  | 0x00        |           1 |          |
|    136 | 0x00 |       250 |     271 |                  | 0x01        |           1 |          |

The full-pad case

| offset | byte | input_len | acc_len | condition_80_inv | padded_byte | is_pad_zone | byte_RLC |
| -----: | :--- | --------: | ------: | ---------------: | :---------- | ----------: | -------- |
|      0 | 0    |       136 |     2   |                0 | 0           |           0 |          |
|      1 | 0xff |       136 |     136 |                0 | 0x80        |           0 |          |
|      2 | 0xff |       136 |     137 |               -1 | 0x00        |           0 |          |
|    ... | ...  |       ... |     ... |              ... | ...         |         ... |          |
|    135 | 0x00 |       136 |     270 |                  | 0x00        |           1 |          |
|    136 | 0x00 |       136 |     271 |                  | 0x01        |           1 |          |


#### Checks

Generally we want these properties:

1. `byte` after `input_len` should be 0, so that prover doesn't cheat about the input length. For exapmle, the prover specify an input length of 100 bytes, so that it shouldn't have a non-zero byte at position 120.
2. The padding `0x80`, `0x01`, or `0x81` are placed at the correct place.

We apply two different checks on the 0~134-th rows and the 135th row.

1. All checks below are only enabled when `state_tag === Finalize`
2. For 0-th row (We use this row for initializing and copying)
   1. `input_len` is copied from the Lookup Region.
   2. `acc_len` is copied from the `perm_count`, and set `next.acc_len === (curr.acc_len - 1) * 136`
   3. `is_pad_zone === 0`
   4. initialize all other columns to be 0
3. For all rows
   1. If `is_pad_zone` then `byte === 0`. `is_pad_zone * byte === 0`
   2. `next.input_len === curr.input_len`
4. For 1~135-th rows
   1. `next.acc_len === curr.acc_len + 1`
   2. Inverse check for `curr.condition_80_inv`
   3. If `curr.input_len - curr.acc_len` is 0, pad `0x80`: `curr.padded_byte === curr.byte + (1 - (curr.input_len - curr.acc_len) * curr.condition_80_inv) * 0x80`
   4. Set `is_pad_zone` to 1 if we entered. `next.is_pad_zone === curr.is_pad_zone + (1 - (next.input_len - next.acc_len) * next.condition_80_inv)`
5. For the 136th row
   1. Same as the previous 0x80 pad, but pad 0x01 if we are in the pad zone. `curr.padded_byte === curr.byte + (1 - (curr.input_len - curr.acc_len) * curr.condition_80_inv) * 0x80 + is_pad_zone * 0x01`
6. Use `byte_RLC` to running sum `byte`. The sum should be equal to `input` in the lookup region
7. `padded_byte` are copied to a word builder gadget to build padded words, which would later be copied to the `Keccak-f` permutation
