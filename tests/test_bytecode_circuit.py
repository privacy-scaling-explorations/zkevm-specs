import traceback
from copy import deepcopy

from zkevm_specs.bytecode import *
from zkevm_specs.evm import Opcode, Bytecode, BytecodeFieldTag, BytecodeTableRow, is_push
from zkevm_specs.util import RLC, rand_fq

# Unroll the bytecode
def unroll(bytecode, randomness):
    return UnrolledBytecode(bytecode, list(Bytecode(bytecode).table_assignments(randomness)))


# Verify the bytecode circuit with the given data
def verify(k, bytecodes, randomness, success):
    push_table = assign_push_table()
    keccak_table = assign_keccak_table(map(lambda v: v.bytes, bytecodes), randomness)
    rows = assign_bytecode_circuit(k, bytecodes, randomness)
    try:
        for (idx, row) in enumerate(rows):
            next_row = rows[(idx + 1) % len(rows)]
            check_bytecode_row(row, next_row, push_table, keccak_table, randomness)
            ok = True
    except AssertionError as e:
        if success:
            traceback.print_exc()
            print(idx)
            print(row)
            print(next_row)
        ok = False
    assert ok == success


k = 10
randomness = rand_fq()


def test_bytecode_unrolling():
    rows = []
    bytecode = []
    # First add all non-push bytes, which should all be seen as code
    for byte in range(256):
        if not is_push(byte):
            bytecode.append(byte)
            rows.append((0, BytecodeFieldTag.Byte, len(rows), True, byte))
    # Now add the different push ops
    for n in range(1, 33):
        data_byte = int(Opcode.PUSH32)
        bytecode.append(Opcode.PUSH1 + n - 1)
        bytecode.extend([data_byte] * n)
        rows.append((0, BytecodeFieldTag.Byte, len(rows), True, Opcode.PUSH1 + n - 1))
        for _ in range(n):
            rows.append((0, BytecodeFieldTag.Byte, len(rows), False, data_byte))
    # Set the hash of the complete bytecode in the rows
    hash = RLC(bytes(reversed(keccak256(bytes(bytecode)))), randomness)
    for i in range(len(rows)):
        rows[i] = BytecodeTableRow(hash.expr(), rows[i][1], rows[i][2], rows[i][3], rows[i][4])
    # Prepend the length of bytecode to rows
    rows.insert(0, BytecodeTableRow(hash.expr(), BytecodeFieldTag.Header, 0, 0, len(bytecode)))
    # Unroll the bytecode
    unrolled = unroll(bytes(bytecode), randomness)
    # Check if the bytecode was unrolled correctly
    assert UnrolledBytecode(bytes(bytecode), rows) == unrolled
    # Verify the unrolling in the circuit
    verify(k, [unrolled], randomness, True)


def test_bytecode_empty():
    bytecodes = [unroll(bytes([]), randomness)]
    verify(k, bytecodes, randomness, True)


def test_bytecode_full():
    bytecodes = [unroll(bytes([7] * (2**k - 1)), randomness)]
    verify(k, bytecodes, randomness, False)  # Last row must be tag=Header


def test_bytecode_incomplete():
    bytecodes = [unroll(bytes([7] * (2**k + 1)), randomness)]
    verify(k, bytecodes, randomness, False)


def test_bytecode_multiple():
    bytecodes = [
        unroll(bytes([]), randomness),
        unroll(bytes([Opcode.PUSH32]), randomness),
        unroll(bytes([Opcode.PUSH32, Opcode.ADD]), randomness),
        unroll(bytes([Opcode.ADD, Opcode.PUSH32]), randomness),
        unroll(bytes([Opcode.ADD, Opcode.PUSH32, Opcode.ADD]), randomness),
    ]
    verify(k, bytecodes, randomness, False)  # Push without data must fail


def test_bytecode_invalid_hash_data():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness)
    verify(k, [unrolled], randomness, True)

    # Change the hash on the first row, i.e. row denoting tag Length
    invalid = deepcopy(unrolled)
    row = unrolled.rows[0]
    invalid.rows[0] = BytecodeTableRow(
        row.bytecode_hash + 1, row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness, False)

    # Change the hash on the second row, i.e. first row with tag Byte
    invalid = deepcopy(unrolled)
    row = unrolled.rows[1]
    invalid.rows[1] = BytecodeTableRow(
        row.bytecode_hash + 1, row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness, False)

    # Change the hash on another position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[4]
    invalid.rows[1] = BytecodeTableRow(
        row.bytecode_hash + 1, row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness, False)

    # Change all the hashes so it doesn't match the keccak lookup hash
    invalid = deepcopy(unrolled)
    for idx, row in enumerate(unrolled.rows):
        invalid.rows[idx] = BytecodeTableRow(1, row.field_tag, row.index, row.is_code, row.value)
    verify(k, [invalid], randomness, False)


def test_bytecode_invalid_index():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness)
    verify(k, [unrolled], randomness, True)

    # Start the index at 1
    invalid = deepcopy(unrolled)
    for idx, row in enumerate(unrolled.rows):
        invalid.rows[idx] = BytecodeTableRow(
            row.bytecode_hash + 1, row.field_tag, row.index, row.is_code, row.value
        )
    verify(k, [invalid], randomness, False)

    # Don't increment an index once
    invalid = deepcopy(unrolled)
    invalid.rows[-1] = BytecodeTableRow(
        invalid.rows[-1].bytecode_hash - 1, row.field_tag, row.index, row.is_code, row.value
    )
    verify(k, [invalid], randomness, False)


def test_bytecode_invalid_byte_data():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), randomness)
    verify(k, [unrolled], randomness, True)

    # Change the first byte in the bytecode
    invalid = deepcopy(unrolled)
    row = unrolled.rows[1]
    invalid.rows[1] = BytecodeTableRow(row.bytecode_hash, row.field_tag, row.index, row.is_code, 9)
    verify(k, [invalid], randomness, False)

    # Change a byte on another position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[5]
    invalid.rows[5] = BytecodeTableRow(row.bytecode_hash, row.field_tag, row.index, row.is_code, 6)
    verify(k, [invalid], randomness, False)

    # Set a byte value out of range
    invalid = deepcopy(unrolled)
    row = unrolled.rows[3]
    invalid.rows[3] = BytecodeTableRow(
        row.bytecode_hash, row.field_tag, row.index, row.is_code, 256
    )
    verify(k, [invalid], randomness, False)


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
        randomness,
    )
    verify(k, [unrolled], randomness, False)  # Push without data must fail

    # The first row, i.e. index == 0 is taken up by the tag Length.
    # Mark the 3rd byte as code (is push data from the first PUSH1)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[3]
    invalid.rows[3] = BytecodeTableRow(row.bytecode_hash, row.field_tag, row.index, 1, row.value)
    verify(k, [invalid], randomness, False)

    # Mark the 4rd byte as data (is code)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[4]
    invalid.rows[4] = BytecodeTableRow(row.bytecode_hash, row.field_tag, row.index, 0, row.value)
    verify(k, [invalid], randomness, False)

    # Mark the 7th byte as code (is data for the PUSH7)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[7]
    invalid.rows[7] = BytecodeTableRow(row.bytecode_hash, row.field_tag, row.index, 1, row.value)
    verify(k, [invalid], randomness, False)
