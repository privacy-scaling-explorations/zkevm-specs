from zkevm_specs.evm.opcode import Opcode, is_push
from zkevm_specs.bytecode import *
import traceback
from copy import deepcopy
from zkevm_specs.evm import Bytecode
from zkevm_specs.util import RLCStore

# Unroll the bytecode
def unroll(bytecode, rlc_store):
    return UnrolledBytecode(bytecode, list(Bytecode(bytecode).table_assignments(rlc_store)))


# Verify the bytecode circuit with the given data
def verify(k, bytecodes, rlc_store, success):
    push_table = assign_push_table()
    keccak_table = assign_keccak_table(map(lambda v: v.bytes, bytecodes), rlc_store)
    rows = assign_bytecode_circuit(k, bytecodes, rlc_store)
    try:
        for (idx, row) in enumerate(rows):
            prev_row = rows[(idx - 1) % len(rows)]
            check_bytecode_row(row, prev_row, push_table, keccak_table, rlc_store.randomness)
            ok = True
    except AssertionError as e:
        if success:
            traceback.print_exc()
        ok = False
    assert ok == success


k = 10
rlc_store = RLCStore()


def test_bytecode_unrolling():
    rows = []
    bytecode = []
    # First add all non-push bytes, which should all be seen as code
    for byte in range(256):
        if not is_push(byte):
            bytecode.append(byte)
            rows.append((0, len(rows), byte, True))
    # Now add the different push ops
    for n in range(1, 33):
        data_byte = int(Opcode.PUSH32)
        bytecode.append(Opcode.PUSH1 + n - 1)
        bytecode.extend([data_byte] * n)
        rows.append((0, len(rows), Opcode.PUSH1 + n - 1, True))
        for _ in range(n):
            rows.append((0, len(rows), data_byte, False))
    # Set the hash of the complete bytecode in the rows
    hash = rlc_store.to_rlc(keccak256(bytes(bytecode)), 32)
    for i in range(len(rows)):
        rows[i] = (hash, rows[i][1], rows[i][2], rows[i][3])
    # Unroll the bytecode
    unrolled = unroll(bytes(bytecode), rlc_store)
    # Check if the bytecode was unrolled correctly
    assert UnrolledBytecode(bytes(bytecode), rows) == unrolled
    # Verify the unrolling in the circuit
    verify(k, [unrolled], rlc_store, True)


def test_bytecode_empty():
    bytecodes = [
        unroll(bytes([]), rlc_store),
    ]
    verify(k, bytecodes, rlc_store, True)


def test_bytecode_full():
    bytecodes = [
        unroll(bytes([7] * 2 ** k), rlc_store),
    ]
    verify(k, bytecodes, rlc_store, True)


def test_bytecode_incomplete():
    bytecodes = [
        unroll(bytes([7] * (2 ** k + 1)), rlc_store),
    ]
    verify(k, bytecodes, rlc_store, False)


def test_bytecode_multiple():
    bytecodes = [
        unroll(bytes([]), rlc_store),
        unroll(bytes([Opcode.PUSH32]), rlc_store),
        unroll(bytes([Opcode.PUSH32, Opcode.ADD]), rlc_store),
        unroll(bytes([Opcode.ADD, Opcode.PUSH32]), rlc_store),
        unroll(bytes([Opcode.ADD, Opcode.PUSH32, Opcode.ADD]), rlc_store),
    ]
    verify(k, bytecodes, rlc_store, True)


def test_bytecode_invalid_hash_data():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), rlc_store)
    verify(k, [unrolled], rlc_store, True)

    # Change the hash on the first position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[0]
    invalid.rows[0] = (row[0] + 1, row[1], row[2], row[3])
    verify(k, [invalid], rlc_store, False)

    # Change the hash on another position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[4]
    invalid.rows[0] = (row[0] + 1, row[1], row[2], row[3])
    verify(k, [invalid], rlc_store, False)

    # Change all the hashes so it doesn't match the keccak lookup hash
    invalid = deepcopy(unrolled)
    for idx, row in enumerate(unrolled.rows):
        invalid.rows[idx] = (1, row[1], row[2], row[3])
    verify(k, [invalid], rlc_store, False)


def test_bytecode_invalid_index():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), rlc_store)
    verify(k, [unrolled], rlc_store, True)

    # Start the index at 1
    invalid = deepcopy(unrolled)
    for idx, row in enumerate(unrolled.rows):
        invalid.rows[idx] = (row[0] + 1, row[1], row[2], row[3])
    verify(k, [invalid], rlc_store, False)

    # Don't increment an index once
    invalid = deepcopy(unrolled)
    row = unrolled.rows[-1]
    invalid.rows[-1] = (row[0] - 1, row[1], row[2], row[3])
    verify(k, [invalid], rlc_store, False)


def test_bytecode_invalid_byte_data():
    unrolled = unroll(bytes([8, 2, 3, 8, 9, 7, 128]), rlc_store)
    verify(k, [unrolled], rlc_store, True)

    # Change the first byte
    invalid = deepcopy(unrolled)
    row = unrolled.rows[0]
    invalid.rows[0] = (row[0], row[1], row[2], 9)
    verify(k, [invalid], rlc_store, False)

    # Change a byte on another position
    invalid = deepcopy(unrolled)
    row = unrolled.rows[5]
    invalid.rows[5] = (row[0], row[1], row[2], 6)
    verify(k, [invalid], rlc_store, False)

    # Set a byte value out of range
    invalid = deepcopy(unrolled)
    row = unrolled.rows[3]
    invalid.rows[3] = (row[0], row[1], row[2], 256)
    verify(k, [invalid], rlc_store, False)


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
        rlc_store,
    )
    verify(k, [unrolled], rlc_store, True)

    # Mark the 3rd byte as code (is push data from the first PUSH1)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[2]
    invalid.rows[2] = (row[0], row[1], 1, row[3])
    verify(k, [invalid], rlc_store, False)

    # Mark the 4rd byte as data (is code)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[3]
    invalid.rows[3] = (row[0], row[1], 0, row[3])
    verify(k, [invalid], rlc_store, False)

    # Mark the 7th byte as code (is data for the PUSH7)
    invalid = deepcopy(unrolled)
    row = unrolled.rows[6]
    invalid.rows[6] = (row[0], row[1], 1, row[3])
    verify(k, [invalid], rlc_store, False)
