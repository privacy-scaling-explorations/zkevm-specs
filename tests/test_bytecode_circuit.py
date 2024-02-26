from copy import deepcopy

from zkevm_specs.bytecode_circuit import *
from zkevm_specs.evm_circuit import (
    Bytecode,
    BytecodeFieldTag,
    BytecodeTableRow,
    Opcode,
    is_push_with_data,
)
from zkevm_specs.util import U256, keccak256
from common import rand_fq


# Unroll the bytecode
def unroll(bytecode: bytes, randomness_keccak: FQ) -> UnrolledBytecode:
    return UnrolledBytecode(bytecode, list(Bytecode(bytearray(bytecode)).table_assignments()))


# Verify the bytecode circuit with the given data
def verify(k: int, bytecodes: Sequence[UnrolledBytecode], randomness_keccak: FQ, success: bool):
    rows = assign_bytecode_circuit(k, bytecodes, randomness_keccak)
    verify_rows(bytecodes, rows, success)


def verify_rows(bytecodes: Sequence[UnrolledBytecode], rows: Sequence[Row], success: bool):
    push_table = assign_push_table()
    keccak_table = assign_keccak_table(list(map(lambda v: v.bytes, bytecodes)), randomness_keccak)
    exception = None
    for idx, row in enumerate(rows):
        try:
            next_row = rows[(idx + 1) % len(rows)]
            check_bytecode_row(row, next_row, push_table, keccak_table, randomness_keccak)
            ok = True
        except AssertionError as e:
            if success:
                print(idx)
                print(row)
                print(next_row)
            exception = e
            break
    if success:
        if exception:
            raise exception
        assert exception is None
    else:
        assert exception is not None


k = 10
randomness_keccak = rand_fq()


def test_bytecode_unrolling():
    rows = []
    bytecode = []
    # First add all non push-with-data bytes, which should all be seen as code
    for byte in range(256):
        if not is_push_with_data(byte):
            bytecode.append(byte)
            rows.append((0, BytecodeFieldTag.Byte, len(rows), True, byte))
    # Now add the different push ops
    for n in range(1, 33):
        data_byte = int(Opcode.PUSH32)
        bytecode.append(Opcode.PUSH0 + n)
        bytecode.extend([data_byte] * n)
        rows.append((0, BytecodeFieldTag.Byte, len(rows), True, Opcode.PUSH0 + n))
        for _ in range(n):
            rows.append((0, BytecodeFieldTag.Byte, len(rows), False, data_byte))
    # Set the hash of the complete bytecode in the rows
    hash = Word(int.from_bytes(keccak256(bytes(bytecode)), "big"))
    for i in range(len(rows)):
        rows[i] = BytecodeTableRow(hash, rows[i][1], rows[i][2], rows[i][3], rows[i][4])
    # Prepend the length of bytecode to rows
    rows.insert(0, BytecodeTableRow(hash, BytecodeFieldTag.Header, FQ(0), FQ(0), FQ(len(bytecode))))
    # Unroll the bytecode
    unrolled = unroll(bytes(bytecode), randomness_keccak)
    # Check if the bytecode was unrolled correctly
    assert UnrolledBytecode(bytes(bytecode), rows) == unrolled
    # Verify the unrolling in the circuit
    verify(k, [unrolled], randomness_keccak, True)


def test_bytecode_empty():
    bytecodes = [unroll(bytes([]), randomness_keccak)]
    verify(k, bytecodes, randomness_keccak, True)


def test_bytecode_full():
    bytecodes = [
        unroll(bytes([7] * (2**k - 2)), randomness_keccak),
        unroll(bytes([]), randomness_keccak),  # Last row must be tag=Header
    ]
    verify(k, bytecodes, randomness_keccak, True)


def test_bytecode_incomplete():
    bytecodes = [unroll(bytes([7] * (2**k + 1)), randomness_keccak)]
    verify(k, bytecodes, randomness_keccak, False)


def test_bytecode_multiple():
    bytecodes = [
        unroll(bytes([]), randomness_keccak),
        unroll(bytes([Opcode.PUSH32]), randomness_keccak),
        unroll(bytes([Opcode.PUSH32, Opcode.ADD]), randomness_keccak),
        unroll(bytes([Opcode.ADD, Opcode.PUSH32]), randomness_keccak),
        unroll(bytes([Opcode.ADD, Opcode.PUSH32, Opcode.ADD]), randomness_keccak),
    ]
    verify(k, bytecodes, randomness_keccak, True)


def test_bytecode_invalid_hash_data():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness_keccak)
    verify(k, [unrolled], randomness_keccak, True)

    # Change the hash on the first row, i.e. row denoting tag Length
    invalid = deepcopy(unrolled)
    row = unrolled.rows[0]
    invalid.rows[0] = BytecodeTableRow(
        Word(row.bytecode_hash.int_value() + 1), row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness_keccak, False)

    # Change the hash on the second row, i.e. first row with tag Byte
    invalid = deepcopy(unrolled)
    row = unrolled.rows[1]
    invalid.rows[1] = BytecodeTableRow(
        Word(row.bytecode_hash.int_value() + 1), row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness_keccak, False)

    # Change the hash on another position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[4]
    invalid.rows[1] = BytecodeTableRow(
        Word(row.bytecode_hash.int_value() + 1), row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness_keccak, False)

    # Change all the hashes so it doesn't match the keccak lookup hash
    invalid = deepcopy(unrolled)
    for idx, row in enumerate(unrolled.rows):
        invalid.rows[idx] = BytecodeTableRow(
            Word(1), row.field_tag, row.index, row.is_code, row.value
        )
    verify(k, [invalid], randomness_keccak, False)


def test_bytecode_invalid_index():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness_keccak)
    verify(k, [unrolled], randomness_keccak, True)

    # Start the index at 1
    invalid = deepcopy(unrolled)
    for idx, row in enumerate(unrolled.rows):
        invalid.rows[idx] = BytecodeTableRow(
            Word(row.bytecode_hash.int_value() + 1),
            row.field_tag,
            row.index,
            row.is_code,
            row.value,
        )
    verify(k, [invalid], randomness_keccak, False)

    # Don't increment an index once
    invalid = deepcopy(unrolled)
    invalid.rows[-1] = BytecodeTableRow(
        Word(invalid.rows[-1].bytecode_hash.int_value() - 1),
        row.field_tag,
        row.index,
        row.is_code,
        row.value,
    )
    verify(k, [invalid], randomness_keccak, False)


def test_bytecode_invalid_byte_data():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness_keccak)
    verify(k, [unrolled], randomness_keccak, True)

    # Change the first byte in the bytecode
    invalid = deepcopy(unrolled)
    row = unrolled.rows[1]
    invalid.rows[1] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, row.is_code, FQ(9)
    )
    verify(k, [invalid], randomness_keccak, False)

    # Change a byte on another position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[5]
    invalid.rows[5] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, row.is_code, FQ(6)
    )
    verify(k, [invalid], randomness_keccak, False)

    # Set a byte value out of range
    invalid = deepcopy(unrolled)
    row = unrolled.rows[3]
    invalid.rows[3] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, row.is_code, FQ(256)
    )
    verify(k, [invalid], randomness_keccak, False)


def test_bytecode_invalid_is_code():
    unrolled = unroll(
        bytes(
            [
                Opcode.ADD,
                Opcode.PUSH1,
                Opcode.PUSH1,
                Opcode.SUB,
                Opcode.PUSH7,
                Opcode.ADD,
                Opcode.PUSH6,
            ]
        ),
        randomness_keccak,
    )
    verify(k, [unrolled], randomness_keccak, True)

    # The first row, i.e. index == 0 is taken up by the tag Length.
    # Mark the 3rd byte as code (is push data from the first PUSH1)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[3]
    invalid.rows[3] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, FQ(1), row.value
    )
    verify(k, [invalid], randomness_keccak, False)

    # Mark the 4th byte as data (is code)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[4]
    invalid.rows[4] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, FQ(0), row.value
    )
    verify(k, [invalid], randomness_keccak, False)

    # Mark the 7th byte as code (is data for the PUSH7)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[7]
    invalid.rows[7] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, FQ(1), row.value
    )
    verify(k, [invalid], randomness_keccak, False)


def test_last_row():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness_keccak)
    verify(k, [unrolled], randomness_keccak, True)

    # last row has length != 0
    rows = assign_bytecode_circuit(k, [unrolled], randomness_keccak)
    rows[-1] = Row(
        q_first=FQ(0),
        q_last=FQ(1),
        hash=Word(EMPTY_HASH),
        tag=FQ(BytecodeFieldTag.Header),
        index=FQ(0),
        value=FQ(0),
        is_code=FQ(False),
        push_data_left=FQ(0),
        value_rlc=FQ(0),
        length=1000,
        push_data_size=FQ(0),
    )
    verify_rows([unrolled], rows, False)

    # last row has hash != EMPTY_HASH
    NOT_EMPTY_HASH = U256(
        int.from_bytes(
            keccak256(bytes("why is there something instead of nothing?", "utf-8")), "big"
        )
    )
    rows = assign_bytecode_circuit(k, [unrolled], randomness_keccak)
    rows[-1] = Row(
        q_first=FQ(0),
        q_last=FQ(1),
        hash=Word(NOT_EMPTY_HASH),
        tag=FQ(BytecodeFieldTag.Header),
        index=FQ(0),
        value=FQ(0),
        is_code=FQ(False),
        push_data_left=FQ(0),
        value_rlc=FQ(0),
        length=FQ(0),
        push_data_size=FQ(0),
    )
    verify_rows([unrolled], rows, False)

    # last row is not Header
    NOT_EMPTY_HASH = U256(
        int.from_bytes(
            keccak256(bytes("why is there something instead of nothing?", "utf-8")), "big"
        )
    )
    rows = assign_bytecode_circuit(k, [unrolled], randomness_keccak)
    rows[-1] = Row(
        q_first=FQ(0),
        q_last=FQ(1),
        hash=Word(NOT_EMPTY_HASH),
        tag=FQ(BytecodeFieldTag.Byte),
        index=FQ(0),
        value=FQ(0),
        is_code=FQ(False),
        push_data_left=FQ(0),
        value_rlc=FQ(0),
        length=FQ(0),
        push_data_size=FQ(0),
    )
    verify_rows([unrolled], rows, False)
