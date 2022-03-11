from itertools import chain
import pytest
from typing import Mapping, Sequence, Tuple

from zkevm_specs.evm import (
    Bytecode,
    CopyCodeToMemoryAuxData,
    ExecutionState,
    RW,
    RWTableTag,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.evm.execution.copy_code_to_memory import MAX_COPY_BYTES
from zkevm_specs.util import rand_fp, RLC, U64


CALL_ID = 1
TESTING_DATA = (
    # single step
    (0x00, 0x00, 54),
    # multi step
    (0x00, 0x40, 123),
    # out of bounds
    (0x10, 0x20, 200),
)


def make_copy_code_step(
    code: Bytecode,
    code_source: RLC,
    buffer_map: Mapping[int, int],
    src_addr: int,
    dst_addr: int,
    src_addr_end: int,
    bytes_left: int,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    rw_counter: int,
) -> Tuple[StepState, Sequence[RW]]:
    aux_data = CopyCodeToMemoryAuxData(
        src_addr=src_addr,
        dst_addr=dst_addr,
        src_addr_end=src_addr_end,
        bytes_left=bytes_left,
        code=code,
    )
    step = StepState(
        execution_state=ExecutionState.CopyCodeToMemory,
        rw_counter=rw_counter,
        call_id=CALL_ID,
        is_root=False,
        program_counter=program_counter,
        stack_pointer=stack_pointer,
        gas_left=0,
        memory_size=memory_size,
        code_source=code_source,
        aux_data=aux_data,
    )
    rws = []
    num_bytes = min(MAX_COPY_BYTES, bytes_left)
    for i in range(num_bytes):
        byte = buffer_map[src_addr + i] if src_addr + i < src_addr_end else 0
        rws.append(
            (
                rw_counter,
                RW.Write,
                RWTableTag.Memory,
                CALL_ID,
                dst_addr + i,
                0,
                byte,
                0,
                0,
                0,
            )
        )
        rw_counter += 1
    return step, rws


def make_copy_code_steps(
    code: Bytecode,
    code_source: RLC,
    src_addr: int,
    dst_addr: int,
    length: int,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    rw_counter: int,
) -> Tuple[Sequence[StepState], Sequence[RW]]:
    buffer_map = dict(zip(range(src_addr, len(code.code)), code.code))
    steps = []
    rws = []
    bytes_left = length
    while bytes_left > 0:
        curr_rw_counter = rws[-1][0] + 1 if rws else rw_counter
        new_step, new_rws = make_copy_code_step(
            code,
            code_source,
            buffer_map,
            src_addr,
            dst_addr,
            len(code.code),
            bytes_left,
            program_counter,
            stack_pointer,
            memory_size,
            curr_rw_counter,
        )
        steps.append(new_step)
        rws.extend(new_rws)
        src_addr += MAX_COPY_BYTES
        dst_addr += MAX_COPY_BYTES
        bytes_left -= MAX_COPY_BYTES
    return steps, rws


def to_word_size(addr: int) -> int:
    return (addr + 31) // 32


@pytest.mark.parametrize("src_addr, dst_addr, length", TESTING_DATA)
def test_copy_code_to_memory(src_addr: U64, dst_addr: U64, length: U64):
    randomness = rand_fp()

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
    print(len(code.code))

    dummy_code = Bytecode().stop()
    code_source = RLC(dummy_code.hash(), randomness)

    next_memory_word_size = to_word_size(dst_addr + length)
    steps, rws = make_copy_code_steps(
        code,
        code_source,
        src_addr,
        dst_addr,
        length,
        program_counter=100,
        memory_size=next_memory_word_size,
        stack_pointer=1024,
        rw_counter=1,
    )
    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rws[-1][0] + 1,
            call_id=CALL_ID,
            is_root=False,
            is_create=False,
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
        bytecode_table=set(code.table_assignments(randomness)).union(
            dummy_code.table_assignments(randomness)
        ),
        rw_table=set(rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )
