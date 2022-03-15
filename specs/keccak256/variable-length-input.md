# Keccak256 For Variable Length Input

We describe the circuit that can process input of arbitrary size.

## Plain Keccak behavior

Keccak256 use a simple iterating sponge construction to handle a variable length input. The sponge absorbs 17 words(136 bytes) of inputs, applies the `Keccak-f` permutation, then absorb next 17 words. Once all parts of the inputs are absorbed, the sponge squeezes out the 32 bytes for the output.

If the last part of the inputs is less than 136 bytes, a padding must be applied. The padding is a multi-rate padding, it pads single bit 1 followed by minimum number of bits 0 followed by a single bit 1, such that the result is 136 bytes.

## Circuit behavior

### Lookup Region

This region splits the input to multiple parts, each part corresponds to their `Keccak-f` permutation round.
This is also a lookup table for the other circuits to lookup the Keccak256 input to the output.

Define:

We use `Round` for the cells of the following columns in a row, it represents the information in a `keccak_f` round.

The `curr: Round` and `next: Round` represent the current and the next row.

Columns:

- `hash_id` Sequential number for grouping different hash
- `input_len` Length for correct padding
- `input` 136 bytes to be absorbed in this round
- `acc_len` How many length we have absorbed
- `acc_input` Accumulatd bytes by random linear combination (in big-endian order)
- `output` The base-2 `state[:4]` output from this round `keccak_f`
- `is_end_result` This flag indicates the hash output is final. The purpose is for external circuit to lookup.

Selector:

- `is_last_round_of_circuit` Last round of the whole circuit (not hash), to avoid `next` wrap around.

#### Checks

1. `hash_id` is sequential `next.id - curr.id in [0, 1]`
2. If we are not in the last round of the circuit or last round of permutation
   1. Checks the `input_len` is  `curr.input_len === next.input_len`
   2. `next.acc_len === curr.acc_len + 136`
   3. `next.acc_len <= curr.input_len`
   4. `next.acc_input === curr.acc_input * (r**136) + RLC(input, r)`
3. If we are in the last round of the circuit or in last round of permutation
   1. Checks the accumulation ends here `assert (curr.input_len - curr.acc_len) in range(136)`
   2. Clear the variables:  `next.acc_len === 0`, `next.acc_input === 0`
4. `is_end_result === next.id - curr.id`

#### Lookup

To lookup the Keccak256 input to the output, query the following columns:

- `is_end_result`: bool
- `input`: RLC
- `output`: RLC

and constrain `is_end_result === 1`

### Padding Region

Note that we define a new `acc_len` which increament byte by byte, where the `acc_len` in the lookup region bumps by 136 bytes.

#### Plain behavior: The padding rule

```python
def get_padding(acc_len) -> bytes:
    """
    output big-endian bytes
    """
    # note that padlen is at maximum 135
    padlen = 136 - acc_len 
    if padlen == 0:
        # no pad
        return []
    elif padlen == 1:
        # pad 0b10000001
        return [0x81]
    elif 1 < padlen < 136:
        return [0x80] + ([0x00] * int(padlen - 2)) + [0x01]
    else:
        raise ValueError("unreachable")
```

#### Circuit

The Padding Region is a 136-row region.

- `byte`
- `input_len` Length for correct padding
- `acc_len` How many bytes we have processed
- `pad_len` 
- `pad_len_inv`
- `pad_val`
- `running_sum`