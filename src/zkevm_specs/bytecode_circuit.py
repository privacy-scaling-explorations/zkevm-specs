from dataclasses import dataclass
from typing import Sequence, Tuple, Set, List
from .util import EMPTY_HASH, FQ, Word
from .evm import get_push_size, BytecodeFieldTag, BytecodeTableRow, KeccakTableRow, KeccakCircuit
from .encoding import is_circuit_code


# Row in the circuit
@dataclass
class Row:
    q_first: FQ
    q_last: FQ
    hash: Word
    tag: FQ
    index: FQ
    value: FQ
    is_code: FQ
    push_data_left: FQ
    value_rlc: FQ
    length: FQ
    push_data_size: FQ


# Unrolled bytecode
@dataclass
class UnrolledBytecode:
    bytes: bytes
    rows: Sequence[BytecodeTableRow]


@is_circuit_code
def check_bytecode_row(
    cur: Row,
    next: Row,
    push_table: Set[Tuple[int, int]],
    keccak_table: Set[Tuple[int, int, int]],
    keccak_randomness: int,
):
    # cur = Row(*[v if isinstance(v, RLC) else FQ(v) for v in cur])
    # next = Row(*[v if isinstance(v, RLC) else FQ(v) for v in next])

    if cur.q_first == 1:
        assert cur.tag == BytecodeFieldTag.Header

    if cur.q_last == 0:
        if cur.tag == BytecodeFieldTag.Header:
            assert cur.value == cur.length
            assert cur.index == 0
            if next.tag == BytecodeFieldTag.Byte:
                check_bytecode_row_header_to_byte(cur, next)
            if next.tag == BytecodeFieldTag.Header:
                check_bytecode_row_header_to_header(cur, keccak_randomness)

        if cur.tag == BytecodeFieldTag.Byte:
            assert (cur.value, cur.push_data_size) in push_table
            assert cur.is_code == FQ(cur.push_data_left == 0)

            if next.tag == BytecodeFieldTag.Byte:
                check_bytecode_row_byte_to_byte(cur, next, keccak_randomness)
            if next.tag == BytecodeFieldTag.Header:
                check_bytecode_row_byte_to_header(cur, keccak_table)

    if cur.q_last == 1:
        assert cur.tag == BytecodeFieldTag.Header
        check_bytecode_row_header_to_header(cur, keccak_randomness)


@is_circuit_code
def check_bytecode_row_header_to_byte(cur: Row, next: Row):
    assert next.length == cur.length
    assert next.index == 0
    assert next.is_code == 1
    assert next.hash == cur.hash
    assert next.value_rlc == next.value


@is_circuit_code
def check_bytecode_row_header_to_header(cur: Row, keccak_randomness: int):
    assert cur.length == 0
    assert cur.hash == Word(EMPTY_HASH), f"{cur.hash} == {Word(EMPTY_HASH)}"


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
def check_bytecode_row_byte_to_header(cur: Row, keccak_table: Set[KeccakTableRow]):
    assert cur.index + 1 == cur.length
    assert KeccakTableRow(FQ(2), cur.value_rlc, cur.length, cur.hash) in keccak_table


# Populate the circuit matrix
def assign_bytecode_circuit(
    k: int, bytecodes: Sequence[UnrolledBytecode], keccak_randomness: FQ
) -> List[Row]:
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
                value_rlc = value_rlc * keccak_randomness + row.value

            # Set the data for this row
            rows.append(
                Row(
                    q_first=FQ(offset == 0),
                    q_last=FQ(offset == last_row_offset),
                    hash=row.bytecode_hash,
                    tag=row.field_tag.expr(),
                    index=row.index.expr(),
                    value=row.value.expr(),
                    is_code=row.is_code.expr(),
                    push_data_left=FQ(push_data_left),
                    value_rlc=FQ(value_rlc),
                    length=FQ(len(bytecode.bytes)),
                    push_data_size=FQ(push_data_size),
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
                q_first=FQ(idx == 0),
                q_last=FQ(idx == last_row_offset),
                hash=Word(EMPTY_HASH),
                tag=FQ(BytecodeFieldTag.Header),
                index=FQ(0),
                value=FQ(0),
                is_code=FQ(False),
                push_data_left=FQ(0),
                value_rlc=FQ(0),
                length=FQ(0),
                push_data_size=FQ(0),
            )
        )

    return rows


# Generate the push table: BYTE -> NUM_PUSHED:
# [0, OpcodeId::PUSH1[ -> 0
# [OpcodeId::PUSH1, OpcodeId::PUSH32] -> [1..32]
# ]OpcodeId::PUSH32, 256[ -> 0
def assign_push_table() -> List[Tuple[FQ, FQ]]:
    push_table = []
    for i in range(256):
        push_table.append((FQ(i), FQ(get_push_size(i))))
    return push_table


# Generate keccak table with row = [input_rlc, input_len, output]
def assign_keccak_table(bytecodes: Sequence[bytes], keccak_randomness: FQ) -> Set[KeccakTableRow]:
    keccak_circuit = KeccakCircuit()
    for bytecode in bytecodes:
        keccak_circuit.add(bytecode, keccak_randomness)
    return set(keccak_circuit.rows)
