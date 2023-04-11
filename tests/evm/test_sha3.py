import pytest

from zkevm_specs.evm_circuit import (
    Block,
    Bytecode,
    CopyCircuit,
    CopyDataTypeTag,
    ExecutionState,
    KeccakCircuit,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.copy_circuit import verify_copy_table
from zkevm_specs.util import (
    keccak256,
    FQ,
    GAS_COST_COPY_SHA3,
    Word,
    U64,
)
from common import memory_expansion, memory_word_size, rand_bytes, rand_fq


CALL_ID = 1
TESTING_DATA = (
    (0x20, 0x40),
    (0x101, 0x202),
    (0x202, 0x00),
)


@pytest.mark.parametrize("offset, length", TESTING_DATA)
def test_sha3(offset: U64, length: U64):
    randomness_keccak = rand_fq()

    # divide rand memory into chunks of 32 which we will push and mstore.
    memory_snapshot = rand_bytes(offset + length)
    memory_chunks = list()
    for i in range(0, len(memory_snapshot), 32):
        memory_chunks.append(memory_snapshot[i : i + 32])
    src_data = dict(
        [
            (i, memory_snapshot[i] if i < len(memory_snapshot) else 0)
            for i in range(offset, offset + length)
        ]
    )

    bytecode = Bytecode()
    for i, chunk in enumerate(memory_chunks):
        bytecode.push(32 * i, n_bytes=32).push(chunk, n_bytes=32).mstore()
    bytecode.push(offset, n_bytes=32).push(length, n_bytes=32).sha3().stop()
    bytecode_hash = Word(bytecode.hash())

    pc = len(memory_chunks) * 67 + 66
    memory_sha3 = keccak256(memory_snapshot[offset : offset + length])
    memory_sha3_word = Word(int.from_bytes(memory_sha3, "big"))
    next_memory_size, memory_expansion_cost = memory_expansion(offset + length, offset + length)
    gas = (
        Opcode.SHA3.constant_gas_cost()
        + memory_expansion_cost
        + memory_word_size(length) * GAS_COST_COPY_SHA3
    )

    offset_word = Word(offset)
    length_word = Word(length)

    rw_dictionary = (
        RWDictionary(1)
        .stack_write(CALL_ID, 1023, length_word)
        .stack_write(CALL_ID, 1022, offset_word)
        .stack_read(CALL_ID, 1022, offset_word)
        .stack_read(CALL_ID, 1023, length_word)
        .stack_write(CALL_ID, 1023, memory_sha3_word)
    )
    rw_counter_interim = rw_dictionary.rw_counter

    copy_circuit = CopyCircuit().copy(
        randomness_keccak,
        rw_dictionary,
        CALL_ID,
        CopyDataTypeTag.Memory,
        CALL_ID,
        CopyDataTypeTag.RlcAcc,
        offset,
        offset + length,
        FQ.zero(),
        length,
        src_data,
    )
    assert rw_dictionary.rw_counter - rw_counter_interim == length

    keccak_circuit = KeccakCircuit().add(
        memory_snapshot[offset : offset + length], randomness_keccak
    )

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
        keccak_table=keccak_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables, randomness_keccak)

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.SHA3,
                rw_counter=3,
                call_id=CALL_ID,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=1022,
                memory_word_size=next_memory_size,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dictionary.rw_counter,
                call_id=CALL_ID,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1023,
                memory_word_size=next_memory_size,
                gas_left=0,
            ),
        ],
    )
