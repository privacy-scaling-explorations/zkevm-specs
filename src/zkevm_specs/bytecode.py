from typing import Sequence, Union, Tuple, Set
from zkevm_specs.util import linear_combine, keccak256, Opcode, fp_add, fp_mul
from collections import namedtuple
from zkevm_specs.encoding import U8, U256, is_circuit_code
from zkevm_specs.util import Opcode, linear_combine, keccak256

# Row in the circuit
Row = namedtuple('Row', 'q_first q_last hash index is_code byte push_rindex hash_rlc hash_length byte_push_size is_final padding')
# Unrolled bytecode
UnrolledBytecode = namedtuple('UnrolledBytecode', 'bytes rows')

@is_circuit_code
def assert_bool(value: Union[int, bool]):
    assert value in [0, 1]

@is_circuit_code
def select(
    selector: U8,
    when_true: U256,
    when_false: U256,
) -> U256:
    return selector * when_true + (1 - selector) * when_false

@is_circuit_code
def check_bytecode_row(
    row: Row,
    prev_row: Row,
    push_table: Set[Tuple[int, int]],
    keccak_table: Set[Tuple[int, int, int]],
    r: int
):
    if not row.q_first and not prev_row.is_final:
        # Continue
        # index needs to increase by 1
        assert(row.index == prev_row.index + 1)
        # is_code := push_rindex_prev == 0
        assert(row.is_code == (prev_row.push_rindex == 0))
        # hash_rlc := hash_rlc_prev * r + byte
        assert(row.hash_rlc == fp_add(fp_mul(prev_row.hash_rlc, r), row.byte))

        # padding needs to remain the the same
        assert(row.padding == prev_row.padding)
        # hash needs to remain the the same
        assert(row.hash == prev_row.hash)
        # hash_length needs to remain the the same
        assert(row.hash_length == prev_row.hash_length)
    else:
        # Start
        # index needs to start at 0
        assert(row.index == 0)
        # is_code needs to be 1 (first byte is always an opcode)
        assert(row.is_code == True)
        # hash_rlc needs to start at byte
        assert(row.hash_rlc == row.byte)

    # is_final needs to be boolean
    assert_bool(row.is_final)
    # padding needs to be boolean
    assert_bool(row.padding)
    # push_rindex := is_code ? byte_push_size : push_rindex_prev - 1
    assert(row.push_rindex == select(row.is_code, row.byte_push_size, prev_row.push_rindex - 1))

    # Padding
    if not row.q_first:
        # padding can only go 0 -> 1 once
        assert_bool(row.padding - prev_row.padding)

    # Last row
    # The hash is checked on the latest row because only then have
    # we accumulated all the bytes. We also have to go through the bytes
    # in a forward manner because that's the only way we can know which
    # bytes are op codes and which are push data.
    if row.q_last:
        # padding needs to be enabled OR
        # the last row needs to be the last byte
        assert(row.padding or row.is_final)

    # Lookup how many bytes the current opcode pushes
    # (also indirectly range checks `byte` to be in [0, 255])
    assert((row.byte, row.byte_push_size) in push_table)

    # keccak lookup when on the last byte
    if row.is_final and not row.padding:
        assert((row.hash_rlc, row.hash_length, row.hash) in keccak_table)


# Populate the circuit matrix
def assign_bytecode_circuit(k, bytecodes, r):

    # All rows are usable in our simulation
    last_row_offset = 2**k - 1

    rows = []
    offset = 0
    for bytecode in bytecodes:
        push_rindex = 0
        hash_rlc = 0
        for idx, row in enumerate(bytecode.rows):
            # Track which byte is an opcode and which is push data
            is_code = push_rindex == 0
            byte_push_size = get_push_size(row[3])
            push_rindex = byte_push_size if is_code else push_rindex - 1

            # Add the byte to the accumulator
            hash_rlc = fp_add(fp_mul(hash_rlc, r), row[3])

            # Set the data for this row
            rows.append(Row(
                offset == 0,
                offset == last_row_offset,
                row[0],
                row[1],
                row[2],
                row[3],
                push_rindex,
                hash_rlc,
                len(bytecode.bytes),
                byte_push_size,
                idx == len(bytecode.bytes) - 1,
                False,
            ))

            offset += 1
            # return when the circuit is full
            if offset == 2**k:
                return rows


    # Padding
    for idx in range(offset, 2**k):
        rows.append(Row(
            idx == 0,
            idx == last_row_offset,
            0,
            0,
            True,
            0,
            0,
            0,
            0,
            0,
            True,
            True,
        ))

    return rows

# Checks if the passed in opcode is a PUSH op
def is_push(op) -> bool:
    return op in range(Opcode.PUSH1, Opcode.PUSH32 + 1)

# Returns how many bytes the opcode pushes
def get_push_size(op) -> int:
    return op - Opcode.PUSH1 + 1 if is_push(op) else 0

# Go through bytecode_source to construct byte code table of spec
# bytecode_table acts as a byte code table by holding
# entry(code_hash, index, is_code, byte)
def assign_bytecode_table(bytecode: bytes, r: int):
    bytecode_table = []
    byte_code_hash = linear_combine(keccak256(bytecode), r)
    # loop to analyze code flag
    push_rindex = 0
    for i in range(len(bytecode)):
        is_code = push_rindex == 0
        push_rindex = get_push_size(bytecode[i]) if is_code else push_rindex - 1
        bytecode_table.append((byte_code_hash, i, is_code, bytecode[i]))

    return bytecode_table

# Generate the push table: BYTE -> NUM_PUSHED:
# [0, OpcodeId::PUSH1[ -> 0
# [OpcodeId::PUSH1, OpcodeId::PUSH32] -> [1..32]
# ]OpcodeId::PUSH32, 256[ -> 0
def assign_push_table():
    push_table = []
    for i in range(256):
        push_table.append((i, get_push_size(i)))
    return push_table

# Generate keccak table
def assign_keccak_table(bytecodes: UnrolledBytecode, r):
    keccak_table = []
    for bytecode in bytecodes:
        hash = linear_combine(keccak256(bytecode.bytes), r)
        rlc = linear_combine(list(reversed(bytecode.bytes)), r)
        keccak_table.append((rlc, len(bytecode.bytes), hash))
    return keccak_table

# Unroll the bytecode
def unroll(bytecode, r):
    return UnrolledBytecode(bytecode, assign_bytecode_table(bytecode, r))
