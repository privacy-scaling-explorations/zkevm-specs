from typing import Sequence, Union, Tuple, Set
from collections import namedtuple
from .util import keccak256, FQ, RLC
from .evm.opcode import get_push_size
from .encoding import U8, U256, is_circuit_code

# Row in the circuit
Row = namedtuple(
    "Row",
    "q_first q_last hash index byte is_code push_data_left hash_rlc hash_length byte_push_size is_final padding",
)
# Unrolled bytecode
UnrolledBytecode = namedtuple("UnrolledBytecode", "bytes rows")


@is_circuit_code
def assert_bool(value: Union[int, bool]):
    assert value in [0, 1]


@is_circuit_code
def select(
    selector: U8,
    when_true: U256,
    when_false: U256,
) -> U256:
    return U256(selector * when_true + (1 - selector) * when_false)


@is_circuit_code
def check_bytecode_row(
    row: Row,
    prev_row: Row,
    push_table: Set[Tuple[int, int]],
    keccak_table: Set[Tuple[int, int, int]],
    r: int,
):
    row = Row(*[v if isinstance(v, RLC) else FQ(v) for v in row])
    prev_row = Row(*[v if isinstance(v, RLC) else FQ(v) for v in prev_row])
    if row.q_first == 0 and prev_row.is_final == 0:
        # Continue
        # index needs to increase by 1
        assert row.index == prev_row.index + 1
        # is_code := push_data_left_prev == 0
        assert row.is_code == (prev_row.push_data_left == 0)
        # hash_rlc := hash_rlc_prev * r + byte
        assert row.hash_rlc == prev_row.hash_rlc * r + row.byte

        # padding needs to remain the same
        assert row.padding == prev_row.padding
        # hash needs to remain the same
        assert row.hash == prev_row.hash
        # hash_length needs to remain the same
        assert row.hash_length == prev_row.hash_length
    else:
        # Start
        # index needs to start at 0
        assert row.index == 0
        # is_code needs to be 1 (first byte is always an opcode)
        assert row.is_code == True
        # hash_rlc needs to start at byte
        assert row.hash_rlc == row.byte

    # is_final needs to be boolean
    assert_bool(row.is_final)
    # padding needs to be boolean
    assert_bool(row.padding)
    # push_data_left := is_code ? byte_push_size : push_data_left_prev - 1
    assert row.push_data_left == select(
        row.is_code, row.byte_push_size, prev_row.push_data_left - 1
    )

    # Padding
    if row.q_first == 0:
        # padding can only go 0 -> 1 once
        assert_bool(row.padding - prev_row.padding)

    # Last row
    # The hash is checked on the latest row because only then have
    # we accumulated all the bytes. We also have to go through the bytes
    # in a forward manner because that's the only way we can know which
    # bytes are op codes and which are push data.
    if row.q_last == 1:
        # padding needs to be enabled OR
        # the last row needs to be the last byte
        assert row.padding == 1 or row.is_final == 1

    # Lookup how many bytes the current opcode pushes
    # (also indirectly range checks `byte` to be in [0, 255])
    assert (row.byte, row.byte_push_size) in push_table

    # keccak lookup when on the last byte
    if row.is_final == 1 and row.padding == 0:
        assert (row.hash_rlc, row.hash_length, row.hash) in keccak_table


# Populate the circuit matrix
def assign_bytecode_circuit(k: int, bytecodes: Sequence[UnrolledBytecode], randomness: int):
    # All rows are usable in this emulation
    last_row_offset = 2**k - 1

    rows = []
    offset = 0
    for bytecode in bytecodes:
        push_data_left = 0
        hash_rlc = FQ(0)
        for idx, row in enumerate(bytecode.rows):
            # Track which byte is an opcode and which is push data
            is_code = push_data_left == 0
            byte_push_size = get_push_size(row[2])
            push_data_left = byte_push_size if is_code else push_data_left - 1

            # Add the byte to the accumulator
            hash_rlc = hash_rlc * randomness + row[2]

            # Set the data for this row
            rows.append(
                Row(
                    offset == 0,
                    offset == last_row_offset,
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    push_data_left,
                    hash_rlc,
                    len(bytecode.bytes),
                    byte_push_size,
                    idx == len(bytecode.bytes) - 1,
                    False,
                )
            )

            offset += 1
            # return when the circuit is full
            if offset == 2**k:
                return rows

    # Padding
    for idx in range(offset, 2**k):
        rows.append(
            Row(
                idx == 0,
                idx == last_row_offset,
                0,
                0,
                0,
                True,
                0,
                0,
                0,
                0,
                True,
                True,
            )
        )

    return rows


# Convert the elements in the table to be either RLC or FQ
def _convert_table(table):
    converted = []
    for row in table:
        converted.append(tuple([v if isinstance(v, RLC) else FQ(v) for v in row]))
    return converted


# Generate the push table: BYTE -> NUM_PUSHED:
# [0, OpcodeId::PUSH1[ -> 0
# [OpcodeId::PUSH1, OpcodeId::PUSH32] -> [1..32]
# ]OpcodeId::PUSH32, 256[ -> 0
def assign_push_table():
    push_table = []
    for i in range(256):
        push_table.append((i, get_push_size(i)))
    return _convert_table(push_table)


# Generate keccak table
def assign_keccak_table(bytecodes: Sequence[bytes], randomness: int):
    keccak_table = []
    for bytecode in bytecodes:
        hash = RLC(bytes(reversed(keccak256(bytecode))), randomness)
        rlc = RLC(bytes(reversed(bytecode)), randomness, len(bytecode))
        keccak_table.append((rlc, len(bytecode), hash))
    return _convert_table(keccak_table)
