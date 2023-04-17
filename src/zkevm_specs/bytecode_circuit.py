from typing import Sequence, Tuple, Set, NamedTuple
from collections import namedtuple
from .util import keccak256, EMPTY_HASH, FQ, RLC
from .evm_circuit import get_push_size, BytecodeFieldTag, BytecodeTableRow
from .encoding import is_circuit_code

# Row in the circuit
Row = namedtuple(
    "Row",
    "q_first q_last hash tag index value is_code push_data_left value_rlc length push_data_size",
)


# Unrolled bytecode
class UnrolledBytecode(NamedTuple):
    bytes: bytes
    rows: Sequence[BytecodeTableRow]


@is_circuit_code
def check_bytecode_row(
    cur: Row,
    next: Row,
    push_table: Set[Tuple[int, int]],
    keccak_table: Set[Tuple[int, int, int]],
    randomness: int,
):
    cur = Row(*[v if isinstance(v, RLC) else FQ(v) for v in cur])
    next = Row(*[v if isinstance(v, RLC) else FQ(v) for v in next])

    if cur.q_first == 1:
        assert cur.tag == BytecodeFieldTag.Header

    if cur.q_last == 0:
        if cur.tag == BytecodeFieldTag.Header:
            assert cur.value == cur.length
            assert cur.index == 0
            if next.tag == BytecodeFieldTag.Byte:
                check_bytecode_row_header_to_byte(cur, next)
            if next.tag == BytecodeFieldTag.Header:
                check_bytecode_row_header_to_header(cur, randomness)

        if cur.tag == BytecodeFieldTag.Byte:
            assert (cur.value, cur.push_data_size) in push_table
            assert cur.is_code == (cur.push_data_left == 0)

            if next.tag == BytecodeFieldTag.Byte:
                check_bytecode_row_byte_to_byte(cur, next, randomness)
            if next.tag == BytecodeFieldTag.Header:
                check_bytecode_row_byte_to_header(cur, keccak_table)

    if cur.q_last == 1:
        assert cur.tag == BytecodeFieldTag.Header
        check_bytecode_row_header_to_header(cur, randomness)


@is_circuit_code
def check_bytecode_row_header_to_byte(cur: Row, next: Row):
    assert next.length == cur.length
    assert next.index == 0
    assert next.is_code == 1
    assert next.hash == cur.hash
    assert next.value_rlc == next.value


@is_circuit_code
def check_bytecode_row_header_to_header(cur: Row, randomness: int):
    assert cur.length == 0
    assert cur.hash == RLC(EMPTY_HASH, FQ(randomness)).expr()


@is_circuit_code
def check_bytecode_row_byte_to_byte(cur: Row, next: Row, r: int):
    assert next.length == cur.length
    assert next.index == cur.index + 1
    assert next.hash == cur.hash
    assert next.value_rlc == cur.value_rlc * r + next.value
    if cur.is_code == 1:
        assert next.push_data_left == cur.push_data_size
    else:
        assert next.push_data_left == cur.push_data_left - 1


@is_circuit_code
def check_bytecode_row_byte_to_header(cur: Row, keccak_table: Set[Tuple[int, int, int]]):
    assert cur.index + 1 == cur.length
    assert (cur.value_rlc, cur.length, cur.hash) in keccak_table


# Populate the circuit matrix
def assign_bytecode_circuit(k: int, bytecodes: Sequence[UnrolledBytecode], randomness: int):
    # All rows are usable in this emulation
    last_row_offset = 2**k - 1

    rows = []
    offset = 0
    for bytecode in bytecodes:
        next_push_data_left = 0
        value_rlc = FQ(0)
        for idx, row in enumerate(bytecode.rows):
            # Subsequent rows represent the bytecode bytes
            # Track which byte is an opcode and which is push data
            push_data_left = next_push_data_left
            is_code = push_data_left == 0
            push_data_size = 0
            if idx > 0:
                push_data_size = get_push_size(row.value)
                next_push_data_left = push_data_size if is_code else push_data_left - 1
                # Add the byte to the accumulator
                value_rlc = value_rlc * randomness + row.value

            # Set the data for this row
            rows.append(
                Row(
                    q_first=offset == 0,
                    q_last=offset == last_row_offset,
                    hash=row.bytecode_hash,
                    tag=row.field_tag,
                    index=row.index,
                    value=row.value,
                    is_code=row.is_code,
                    push_data_left=push_data_left,
                    value_rlc=value_rlc,
                    length=len(bytecode.bytes),
                    push_data_size=push_data_size,
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
                q_first=idx == 0,
                q_last=idx == last_row_offset,
                hash=RLC(EMPTY_HASH, FQ(randomness)).expr(),
                tag=BytecodeFieldTag.Header,
                index=0,
                value=0,
                is_code=False,
                push_data_left=0,
                value_rlc=0,
                length=0,
                push_data_size=0,
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
# [0, OpcodeId::PUSH1] -> 0
# [OpcodeId::PUSH1, OpcodeId::PUSH32] -> [1..32]
# [OpcodeId::PUSH32, 256] -> 0
def assign_push_table():
    push_table = []
    for i in range(256):
        push_table.append((i, get_push_size(i)))
    return _convert_table(push_table)


# Generate keccak table
def assign_keccak_table(bytecodes: Sequence[bytes], randomness: FQ):
    keccak_table = []
    for bytecode in bytecodes:
        hash = RLC(bytes(reversed(keccak256(bytecode))), randomness)
        rlc = RLC(bytes(reversed(bytecode)), randomness, len(bytecode))
        keccak_table.append((rlc.expr(), len(bytecode), hash.expr()))
    return _convert_table(keccak_table)
