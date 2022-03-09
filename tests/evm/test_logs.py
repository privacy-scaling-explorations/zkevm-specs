import pytest
from typing import Sequence, Tuple, Mapping, Optional

from zkevm_specs.evm import (
    Opcode,
    ExecutionState,
    StepState,
    CopyToLogAuxData,
    verify_steps,
    Tables,
    RWTableTag,
    CallContextFieldTag,
    TxLogFieldTag,
    RW,
    RLC,
    Block,
    Transaction,
    Bytecode,
    GAS_COST_LOG,
)
from zkevm_specs.evm.execution.copy_to_log import MAX_COPY_BYTES
from zkevm_specs.util import (
    rand_fp,
    rand_bytes,
    U64,
    U256,
    rand_address,
    memory_expansion,
    MEMORY_EXPANSION_QUAD_DENOMINATOR,
)


CALL_ID = 1
TX_ID = 2
CALLEE_ADDRESS = rand_address()

bytecodes = [
    Bytecode().log0(),
    Bytecode().log1(),
    Bytecode().log2(),
    Bytecode().log3(),
    Bytecode().log4(),
]

TESTING_DATA = (
    # zero topic(log0)
    ([], 10, 2),
    # one topic(log1)
    ([0x030201], 20, 3),
    # two topics(log2)
    ([0x030201, 0x0F0E0D], 100, 20),
    # three topics(log3)
    ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50),
    # four topics(log4)
    ([0x030201, 0x0F0E0D, 0x0D8F01, 0x0AA213], 421, 15),
)


def make_log_copy_step(
    buffer_map: Mapping[int, int],
    src_addr: int,
    src_addr_end: int,
    bytes_left: int,
    rw_counter: int,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    gas_left: int,
    code_source: RLC,
    state_write_counter: int,
    log_index: int,
) -> Tuple[StepState, Sequence[RW]]:
    aux_data = CopyToLogAuxData(
        src_addr=src_addr,
        src_addr_end=src_addr_end,
        bytes_left=bytes_left,
    )
    step = StepState(
        execution_state=ExecutionState.CopyToLog,
        rw_counter=rw_counter,
        call_id=1,
        program_counter=program_counter,
        stack_pointer=stack_pointer,
        gas_left=gas_left,
        memory_size=memory_size,
        code_source=code_source,
        log_index=log_index,
        state_write_counter=state_write_counter,
        aux_data=aux_data,
    )

    rws = []
    num_bytes = min(MAX_COPY_BYTES, bytes_left)
    for i in range(num_bytes):
        byte = buffer_map[src_addr + i] if src_addr + i < src_addr_end else 0
        if src_addr + i < src_addr_end:
            rws.append(
                (
                    rw_counter,
                    RW.Read,
                    RWTableTag.Memory,
                    CALL_ID,
                    src_addr + i,
                    0,
                    byte,
                    0,
                    0,
                    0,
                )
            )
            rw_counter += 1
            rws.append(
                (
                    rw_counter,
                    RW.Write,
                    RWTableTag.TxLog,
                    log_index,
                    i,
                    TxLogFieldTag.Data,
                    byte,
                    0,
                    0,
                    0,
                )
            )
        rw_counter += 1
    return step, rws


def make_log_copy_steps(
    buffer: bytes,
    buffer_addr: int,
    src_addr: int,
    length: int,
    rw_counter: int,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    gas_left: int,
    code_source: RLC,
    state_write_counter: int,
    log_index: int,
) -> Tuple[Sequence[StepState], Sequence[RW]]:
    buffer_addr_end = buffer_addr + len(buffer)
    buffer_map = dict(zip(range(buffer_addr, buffer_addr_end), buffer))
    steps = []
    rws = []
    bytes_left = length
    while bytes_left > 0:
        curr_rw_counter = rws[-1][0] + 1 if rws else rw_counter
        new_step, new_rws = make_log_copy_step(
            buffer_map,
            src_addr,
            buffer_addr_end,
            bytes_left,
            curr_rw_counter,
            program_counter,
            stack_pointer,
            memory_size,
            gas_left,
            code_source,
            state_write_counter,
            log_index,
        )
        steps.append(new_step)
        rws.extend(new_rws)
        src_addr += MAX_COPY_BYTES
        bytes_left -= MAX_COPY_BYTES
    return steps, rws


@pytest.mark.parametrize("topics, mstart, msize", TESTING_DATA)
def test_logs(topics: list, mstart: U64, msize: U64):
    randomness = rand_fp()
    data = rand_bytes(msize)

    topic_count = len(topics)
    next_memory_size, memory_expansion_cost = memory_expansion(mstart, msize)
    dynamic_gas = GAS_COST_LOG * topic_count + 8 * msize + memory_expansion_cost

    bytecode = bytecodes[topic_count]
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tx = Transaction(id=TX_ID, gas=dynamic_gas)

    steps = [
        StepState(
            execution_state=ExecutionState.LOG,
            rw_counter=1,
            call_id=CALL_ID,
            is_root=False,
            is_create=False,
            code_source=bytecode_hash,
            program_counter=0,
            stack_pointer=1015,
            memory_size=mstart,
            gas_left=dynamic_gas,
            log_index=0,
            state_write_counter=0,
        )
    ]
    rws = [
        (1, RW.Read, RWTableTag.Stack, 1, 1015, 0, RLC(mstart, randomness, 8), 0, 0, 0),
        (2, RW.Read, RWTableTag.Stack, 1, 1016, 0, RLC(msize, randomness, 8), 0, 0, 0),
        (
            3,
            RW.Read,
            RWTableTag.CallContext,
            1,
            CallContextFieldTag.CalleeAddress,
            0,
            CALLEE_ADDRESS,
            0,
            0,
            0,
        ),
        (
            4,
            RW.Write,
            RWTableTag.TxLog,
            0,
            0,
            TxLogFieldTag.Address,
            CALLEE_ADDRESS,
            0,
            0,
            0,
        ),
        (
            5,
            RW.Read,
            RWTableTag.CallContext,
            1,
            CallContextFieldTag.IsStatic,
            0,
            0,
            0,
            0,
            0,
        ),
    ]

    # append topic rows
    rws.extend(construct_topic_rws(6, 1017, topics, randomness))
    new_steps, new_rws = make_log_copy_steps(
        data,
        mstart,
        mstart,
        msize,
        rw_counter=rws[-1][0] + 1,
        program_counter=1,
        memory_size=next_memory_size,
        stack_pointer=1015 + (2 + topic_count),
        gas_left=0,
        code_source=bytecode_hash,
        state_write_counter=1,
        log_index=1,
    )
    # append memory & log steps and rows
    steps.extend(new_steps)
    rws.extend(new_rws)

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rws[-1][0] + 1,
            call_id=CALL_ID,
            is_root=False,
            is_create=False,
            code_source=bytecode_hash,
            program_counter=1,
            stack_pointer=1015 + (2 + topic_count),
            memory_size=next_memory_size,
            gas_left=0,
            state_write_counter=1,
            log_index=1,
        )
    )

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )


# helper to construct topics rows of RW table
def construct_topic_rws(gc: U256, sp: int, topics: list, randomness: int):
    rows = []
    for i in range(len(topics)):
        rows.append(
            (gc, RW.Read, RWTableTag.Stack, 1, sp, 0, RLC(topics[i], randomness, 32), 0, 0, 0)
        )
        rows.append(
            (
                gc + 1,
                RW.Write,
                RWTableTag.TxLog,
                0,
                i,
                TxLogFieldTag.Topics,
                RLC(topics[i], randomness, 32),
                0,
                0,
                0,
            )
        )
        sp += 1
        gc += 2
    return rows
