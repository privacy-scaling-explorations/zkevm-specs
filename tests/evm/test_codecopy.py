from itertools import chain
import pytest
from typing import Mapping, Sequence, Tuple

from zkevm_specs.evm import (
    AccountFieldTag,
    Bytecode,
    CallContextFieldTag,
    CopyCodeToMemoryAuxData,
    ExecutionState,
    Opcode,
    RW,
    RWDictionary,
    RWTableTag,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import (
    GAS_COST_COPY,
    FQ,
    MAX_N_BYTES_COPY_CODE_TO_MEMORY,
    MEMORY_EXPANSION_LINEAR_COEFF,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
    RLC,
    U64,
    rand_address,
    rand_fq,
)


CALL_ID = 1
TESTING_DATA = (
    # single step
    (0x00, 0x00, 54),
    # multi step
    (0x00, 0x40, 123),
    # out of bounds
    (0x10, 0x20, 200),
)


def to_word_size(addr: int) -> int:
    return (addr + 31) // 32


def memory_gas_cost(memory_word_size: int) -> int:
    quad_cost = memory_word_size * memory_word_size // MEMORY_EXPANSION_QUAD_DENOMINATOR
    linear_cost = memory_word_size * MEMORY_EXPANSION_LINEAR_COEFF
    return quad_cost + linear_cost


def memory_copier_gas_cost(
    curr_memory_word_size: int, next_memory_word_size: int, length: int
) -> int:
    curr_memory_cost = memory_gas_cost(curr_memory_word_size)
    next_memory_cost = memory_gas_cost(next_memory_word_size)
    return to_word_size(length) * GAS_COST_COPY + next_memory_cost - curr_memory_cost


def make_copy_code_step(
    code: Bytecode,
    code_source: RLC,
    buffer_map: Mapping[int, int],
    src_addr: int,
    dst_addr: int,
    src_addr_end: int,
    bytes_left: int,
    rw_dictionary: RWDictionary,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    randomness: FQ,
) -> StepState:
    aux_data = CopyCodeToMemoryAuxData(
        src_addr=src_addr,
        dst_addr=dst_addr,
        src_addr_end=src_addr_end,
        bytes_left=bytes_left,
        code_source=RLC(code.hash(), randomness),
    )
    step = StepState(
        execution_state=ExecutionState.CopyCodeToMemory,
        rw_counter=rw_dictionary.rw_counter,
        call_id=CALL_ID,
        is_root=True,
        program_counter=program_counter,
        stack_pointer=stack_pointer,
        gas_left=0,
        memory_size=memory_size,
        code_source=code_source,
        aux_data=aux_data,
    )

    num_bytes = min(MAX_N_BYTES_COPY_CODE_TO_MEMORY, bytes_left)
    for i in range(num_bytes):
        byte = buffer_map[src_addr + i] if src_addr + i < src_addr_end else 0
        rw_dictionary.memory_write(CALL_ID, dst_addr + i, byte)
    return step


def make_copy_code_steps(
    code: Bytecode,
    code_source: RLC,
    src_addr: int,
    dst_addr: int,
    length: int,
    rw_dictionary: RWDictionary,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    randomness: FQ,
) -> Sequence[StepState]:
    buffer_map = dict(zip(range(src_addr, len(code.code)), code.code))
    steps = []
    bytes_left = length
    while bytes_left > 0:
        new_step = make_copy_code_step(
            code,
            code_source,
            buffer_map,
            src_addr,
            dst_addr,
            len(code.code),
            bytes_left,
            rw_dictionary,
            program_counter,
            stack_pointer,
            memory_size,
            randomness,
        )
        steps.append(new_step)
        src_addr += MAX_N_BYTES_COPY_CODE_TO_MEMORY
        dst_addr += MAX_N_BYTES_COPY_CODE_TO_MEMORY
        bytes_left -= MAX_N_BYTES_COPY_CODE_TO_MEMORY
    return steps


@pytest.mark.parametrize("src_addr, dst_addr, length", TESTING_DATA)
def test_codecopy(src_addr: U64, dst_addr: U64, length: U64):
    randomness = rand_fq()

    length_rlc = RLC(length, randomness)
    src_addr_rlc = RLC(src_addr, randomness)
    dst_addr_rlc = RLC(dst_addr, randomness)

    code = Bytecode().push32(length_rlc).push32(src_addr_rlc).push32(dst_addr_rlc).codecopy().stop()

    code_source = RLC(code.hash(), randomness)
    next_memory_word_size = to_word_size(dst_addr + length)

    gas_cost_push32 = Opcode.PUSH32.constant_gas_cost()
    gas_cost_codecopy = Opcode.CODECOPY.constant_gas_cost() + memory_copier_gas_cost(
        0, next_memory_word_size, length
    )
    total_gas_cost = gas_cost_codecopy + (3 * gas_cost_push32)

    rw_dictionary = (
        RWDictionary(1)
        .stack_write(CALL_ID, 1023, length_rlc)
        .stack_write(CALL_ID, 1022, src_addr_rlc)
        .stack_write(CALL_ID, 1021, dst_addr_rlc)
        .stack_read(CALL_ID, 1021, dst_addr_rlc)
        .stack_read(CALL_ID, 1022, src_addr_rlc)
        .stack_read(CALL_ID, 1023, length_rlc)
    )
    # rw counter before memory writes
    rw_counter_interim = rw_dictionary.rw_counter

    steps = [
        StepState(
            execution_state=ExecutionState.PUSH,
            rw_counter=1,
            call_id=CALL_ID,
            is_root=True,
            code_source=code_source,
            program_counter=0,
            stack_pointer=1024,
            gas_left=total_gas_cost,
        ),
        StepState(
            execution_state=ExecutionState.PUSH,
            rw_counter=2,
            call_id=CALL_ID,
            is_root=True,
            code_source=code_source,
            program_counter=33,
            stack_pointer=1023,
            gas_left=total_gas_cost - gas_cost_push32,
        ),
        StepState(
            execution_state=ExecutionState.PUSH,
            rw_counter=3,
            call_id=CALL_ID,
            is_root=True,
            code_source=code_source,
            program_counter=66,
            stack_pointer=1022,
            gas_left=total_gas_cost - 2 * gas_cost_push32,
        ),
        StepState(
            execution_state=ExecutionState.CODECOPY,
            rw_counter=4,
            call_id=CALL_ID,
            is_root=True,
            code_source=code_source,
            program_counter=99,
            stack_pointer=1021,
            gas_left=gas_cost_codecopy,
        ),
    ]

    steps_internal = make_copy_code_steps(
        code,
        code_source,
        src_addr,
        dst_addr,
        length,
        rw_dictionary=rw_dictionary,
        program_counter=100,
        stack_pointer=1024,
        memory_size=next_memory_word_size,
        randomness=randomness,
    )
    steps.extend(steps_internal)

    # rw counter post memory writes
    rw_counter_final = rw_dictionary.rw_counter
    assert rw_counter_final - rw_counter_interim == length

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=True,
            code_source=code_source,
            program_counter=100,
            stack_pointer=1024,
            memory_size=next_memory_word_size,
            gas_left=0,
        )
    )

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(code.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )


@pytest.mark.parametrize("src_addr, dst_addr, length", TESTING_DATA)
def test_copy_code_to_memory(src_addr: U64, dst_addr: U64, length: U64):
    randomness = rand_fq()

    code = (
        Bytecode()
        .push32(0x123)
        .pop()
        .push32(0x213)
        .pop()
        .push32(0x321)
        .pop()
        .push32(0x12349AB)
        .pop()
        .push32(0x1928835)
        .pop()
    )

    dummy_code = Bytecode().stop()
    code_source = RLC(dummy_code.hash(), randomness)

    rw_dictionary = RWDictionary(1)

    next_memory_word_size = to_word_size(dst_addr + length)
    steps = make_copy_code_steps(
        code,
        code_source,
        src_addr,
        dst_addr,
        length,
        rw_dictionary=rw_dictionary,
        program_counter=0,
        memory_size=next_memory_word_size,
        stack_pointer=1024,
        randomness=randomness,
    )
    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=True,
            is_create=False,
            code_source=code_source,
            program_counter=0,
            stack_pointer=1024,
            memory_size=next_memory_word_size,
            gas_left=0,
        )
    )

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(code.table_assignments(randomness)).union(
            dummy_code.table_assignments(randomness)
        ),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )
