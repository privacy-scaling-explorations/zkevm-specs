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
    RWDictionary,
)
from zkevm_specs.evm.execution.copy_to_log import MAX_COPY_BYTES
from zkevm_specs.util import (
    rand_fq,
    rand_bytes,
    U64,
    U256,
    rand_address,
    memory_expansion,
    FQ,
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
    # is_persistent = true cases
    # zero topic(log0)
    ([], 10, 2, 1),
    # one topic(log1)
    ([0x030201], 20, 3, 1),
    # two topics(log2)
    ([0x030201, 0x0F0E0D], 100, 20, 1),
    # three topics(log3)
    ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, 1),
    # four topics(log4)
    ([0x030201, 0x0F0E0D, 0x0D8F01, 0x0AA213], 421, 15, 1),
    # is_persistent = false cases
    # zero topic(log0)
    ([], 10, 2, 0),
    # one topic(log1)
    ([0x030201], 20, 3, 0),
    # two topics(log2)
    ([0x030201, 0x0F0E0D], 100, 20, 0),
    # three topics(log3)
    ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, 0),
    # four topics(log4)
    ([0x030201, 0x0F0E0D, 0x0D8F01, 0x0AA213], 421, 15, 0),
)


def make_log_copy_step(
    buffer_map: Mapping[int, int],
    src_addr: int,
    src_addr_end: int,
    bytes_left: int,
    data_start_index: int,
    rw_dictionary: RWDictionary,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    gas_left: int,
    code_hash: RLC,
    log_id: int,
    is_persistent: bool,
) -> Tuple[StepState, Sequence[RW]]:
    aux_data = CopyToLogAuxData(
        src_addr=src_addr,
        src_addr_end=src_addr_end,
        bytes_left=bytes_left,
        is_persistent=is_persistent,
        tx_id=TX_ID,
        data_start_index=data_start_index,
    )
    step = StepState(
        execution_state=ExecutionState.CopyToLog,
        rw_counter=rw_dictionary.rw_counter,
        call_id=CALL_ID,
        program_counter=program_counter,
        stack_pointer=stack_pointer,
        gas_left=gas_left,
        memory_size=memory_size,
        code_hash=code_hash,
        log_id=is_persistent,
        aux_data=aux_data,
    )
    num_bytes = min(MAX_COPY_BYTES, bytes_left)
    for i in range(num_bytes):
        byte = buffer_map[src_addr + i] if src_addr + i < src_addr_end else 0
        if src_addr + i < src_addr_end:
            rw_dictionary.memory_read(CALL_ID, src_addr + i, FQ(byte))
            if is_persistent:
                rw_dictionary.tx_log_write(
                    TX_ID, log_id, TxLogFieldTag.Data, i + data_start_index, FQ(byte)
                )

    return step


def make_log_copy_steps(
    buffer: bytes,
    buffer_addr: int,
    src_addr: int,
    length: int,
    rw_dictionary: RWDictionary,
    program_counter: int,
    stack_pointer: int,
    memory_size: int,
    gas_left: int,
    code_hash: RLC,
    log_id: int,
    is_persistent: bool,
) -> Sequence[StepState]:
    buffer_addr_end = buffer_addr + len(buffer)
    buffer_map = dict(zip(range(buffer_addr, buffer_addr_end), buffer))
    steps = []
    bytes_left = length
    data_start_index = 0
    while bytes_left > 0:
        new_step = make_log_copy_step(
            buffer_map,
            src_addr,
            buffer_addr_end,
            bytes_left,
            data_start_index,
            rw_dictionary,
            program_counter,
            stack_pointer,
            memory_size,
            gas_left,
            code_hash,
            log_id,
            is_persistent,
        )
        steps.append(new_step)
        src_addr += MAX_COPY_BYTES
        data_start_index += MAX_COPY_BYTES
        bytes_left -= MAX_COPY_BYTES
    return steps


@pytest.mark.parametrize("topics, mstart, msize, is_persistent", TESTING_DATA)
def test_logs(topics: list, mstart: U64, msize: U64, is_persistent: bool):
    randomness = rand_fq()
    data = rand_bytes(msize)
    topic_count = len(topics)
    next_memory_size, memory_expansion_cost = memory_expansion(mstart, msize)
    dynamic_gas = GAS_COST_LOG + GAS_COST_LOG * topic_count + 8 * msize + memory_expansion_cost
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
            code_hash=bytecode_hash,
            program_counter=0,
            stack_pointer=1015,
            memory_size=mstart,
            gas_left=dynamic_gas,
            log_id=0,
        )
    ]

    rw_dictionary = (
        RWDictionary(1)
        .stack_read(CALL_ID, 1015, RLC(mstart, randomness))
        .stack_read(CALL_ID, 1016, RLC(msize, randomness))
        .call_context_read(CALL_ID, CallContextFieldTag.TxId, TX_ID)
        .call_context_read(CALL_ID, CallContextFieldTag.IsStatic, FQ(0))
        .call_context_read(CALL_ID, CallContextFieldTag.CalleeAddress, FQ(CALLEE_ADDRESS))
        .call_context_read(CALL_ID, CallContextFieldTag.IsPersistent, is_persistent)
    )

    if is_persistent:
        rw_dictionary.tx_log_write(TX_ID, 1, TxLogFieldTag.Address, 0, FQ(CALLEE_ADDRESS))

    # append topic rows
    construct_topic_rws(rw_dictionary, 1017, topics, is_persistent, randomness)
    new_steps = make_log_copy_steps(
        data,
        mstart,
        mstart,
        msize,
        rw_dictionary=rw_dictionary,
        program_counter=1,
        memory_size=next_memory_size,
        stack_pointer=1015 + (2 + topic_count),
        gas_left=0,
        code_hash=bytecode_hash,
        log_id=1,
        is_persistent=is_persistent,
    )
    # append memory & log steps and rows
    steps.extend(new_steps)
    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=False,
            is_create=False,
            code_hash=bytecode_hash,
            program_counter=1,
            stack_pointer=1015 + (2 + topic_count),
            memory_size=next_memory_size,
            gas_left=0,
            log_id=is_persistent,
        )
    )
    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
    )
    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )


# helper to construct topics rows of RW table
def construct_topic_rws(
    rw_dictionary: RWDictionary,
    sp: int,
    topics: list,
    is_persistent: bool,
    randomness: int,
):
    for i in range(len(topics)):
        rw_dictionary.stack_read(CALL_ID, sp, RLC(topics[i], randomness, 32))
        if is_persistent:
            rw_dictionary.tx_log_write(
                TX_ID, 1, TxLogFieldTag.Topic, i, RLC(topics[i], randomness, 32)
            )

        sp += 1
