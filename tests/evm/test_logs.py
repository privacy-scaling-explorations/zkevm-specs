import pytest
from typing import Sequence, Tuple, Mapping, Optional
from zkevm_specs.evm import (
    Opcode,
    ExecutionState,
    StepState,
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
    GAS_COST_LOGDATA,
    RWDictionary,
    CopyCircuit,
    CopyDataTypeTag,
)
from zkevm_specs.copy_circuit import verify_copy_table
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

SINGLE_LOG_TESTING_DATA = (
    # is_persistent = true cases
    # zero topic(log0)
    ([], 10, 2, True),
    # one topic(log1)
    ([0x030201], 20, 3, True),
    # two topics(log2)
    ([0x030201, 0x0F0E0D], 100, 20, True),
    # three topics(log3)
    ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, True),
    # four topics(log4)
    ([0x030201, 0x0F0E0D, 0x0D8F01, 0x0AA213], 421, 15, True),
    # is_persistent = false cases
    # zero topic(log0)
    ([], 10, 2, False),
    # one topic(log1)
    ([0x030201], 20, 3, False),
    # two topics(log2)
    ([0x030201, 0x0F0E0D], 100, 20, False),
    # three topics(log3)
    ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, False),
    # four topics(log4)
    ([0x030201, 0x0F0E0D, 0x0D8F01, 0x0AA213], 421, 15, False),
)

MULTI_LOGS_TESTING_DATA = (
    (
        ([], 10, 2, True),
        ([0x030201, 0x0F0E0D], 100, 20, True),
    ),
    (
        ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, True),
        ([0x030201], 20, 3, False),
    ),
    (
        ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, True),
        ([0x030201], 20, 3, False),
        ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, True),
    ),
    (
        ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, True),
        ([0x030201], 20, 3, True),
        ([0x030201, 0x0F0E0D, 0x0D8F01], 180, 50, True),
    ),
)


def log_code(bytecode: Bytecode, num_topic: int):
    if num_topic == 0:
        bytecode.log0()
    elif num_topic == 1:
        bytecode.log1()
    elif num_topic == 2:
        bytecode.log2()
    elif num_topic == 3:
        bytecode.log3()
    elif num_topic == 4:
        bytecode.log4()
    else:
        raise ValueError(f"Incorrect number of topics: {num_topic}")


# helper to construct topics rows of RW table
def construct_topic_rws(
    rw_dictionary: RWDictionary,
    log_id: int,
    sp: int,
    topics: list,
    is_persistent: bool,
    randomness: int,
):
    for i in range(len(topics)):
        rw_dictionary.stack_read(CALL_ID, sp, RLC(topics[i], randomness, 32))
        if is_persistent:
            rw_dictionary.tx_log_write(
                TX_ID, log_id, TxLogFieldTag.Topic, i, RLC(topics[i], randomness, 32)
            )

        sp += 1


def make_log(
    rw_dictionary: RWDictionary,
    copy_circuit: CopyCircuit,
    randomness: FQ,
    stack_pointer: int,
    log_id: int,
    topics: list,
    mstart: U64,
    msize: U64,
    is_persistent: bool,
):
    data = rand_bytes(msize)
    (
        rw_dictionary.stack_read(CALL_ID, stack_pointer, RLC(mstart, randomness))
        .stack_read(CALL_ID, stack_pointer + 1, RLC(msize, randomness))
        .call_context_read(CALL_ID, CallContextFieldTag.TxId, TX_ID)
        .call_context_read(CALL_ID, CallContextFieldTag.IsStatic, 0)
        .call_context_read(CALL_ID, CallContextFieldTag.CalleeAddress, FQ(CALLEE_ADDRESS))
        .call_context_read(CALL_ID, CallContextFieldTag.IsPersistent, is_persistent)
    )

    if is_persistent:
        rw_dictionary.tx_log_write(TX_ID, log_id, TxLogFieldTag.Address, 0, FQ(CALLEE_ADDRESS))

    # append topic rows
    construct_topic_rws(rw_dictionary, log_id, stack_pointer + 2, topics, is_persistent, randomness)

    # copy the log data
    src_data = dict([(mstart + i, byte) for (i, byte) in enumerate(data)])
    if is_persistent:
        copy_circuit.copy(
            rw_dictionary,
            CALL_ID,
            CopyDataTypeTag.Memory,
            TX_ID,
            CopyDataTypeTag.TxLog,
            mstart,
            mstart + msize,
            0,
            msize,
            src_data,
            log_id=log_id,
        )
    return stack_pointer + 2 + len(topics)


@pytest.mark.parametrize("topics, mstart, msize, is_persistent", SINGLE_LOG_TESTING_DATA)
def test_single_log(topics: list, mstart: U64, msize: U64, is_persistent: bool):
    randomness = rand_fq()
    # init bytecode
    bytecode = Bytecode()
    log_code(bytecode, len(topics))
    bytecode.stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    rw_dictionary = RWDictionary(1)
    copy_circuit = CopyCircuit()

    next_memory_size, memory_expansion_cost = memory_expansion(0, mstart + msize)
    dynamic_gas = (
        GAS_COST_LOG + GAS_COST_LOG * len(topics) + GAS_COST_LOGDATA * msize + memory_expansion_cost
    )
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
            memory_size=0,
            gas_left=dynamic_gas,
            log_id=0,
        )
    ]
    sp = make_log(
        rw_dictionary, copy_circuit, randomness, 1015, 1, topics, mstart, msize, is_persistent
    )

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=False,
            is_create=False,
            code_hash=bytecode_hash,
            program_counter=1,
            stack_pointer=sp,
            memory_size=next_memory_size,
            gas_left=0,
            log_id=is_persistent,
        )
    )

    tx = Transaction(id=TX_ID, gas=dynamic_gas)
    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )
    verify_copy_table(copy_circuit, tables)
    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )


@pytest.mark.parametrize("log_entries", MULTI_LOGS_TESTING_DATA)
def test_multi_logs(log_entries):
    randomness = rand_fq()
    # init bytecode
    bytecode = Bytecode()
    total_gas = 0
    for topics, _, msize, _ in log_entries:
        log_code(bytecode, len(topics))
        total_gas += GAS_COST_LOG + GAS_COST_LOG * len(topics) + GAS_COST_LOGDATA * msize
    bytecode.stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tx = Transaction(id=TX_ID, gas=total_gas)
    steps = []
    rw_dictionary = RWDictionary(1)
    copy_circuit = CopyCircuit()

    stack_pointer = 1000
    log_id = 0
    gas_left = total_gas
    for pc, (topics, mstart, msize, is_persistent) in enumerate(log_entries):
        steps.append(
            StepState(
                execution_state=ExecutionState.LOG,
                rw_counter=rw_dictionary.rw_counter,
                call_id=CALL_ID,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                memory_size=50,
                gas_left=gas_left,
                log_id=log_id,
            )
        )
        stack_pointer = make_log(
            rw_dictionary,
            copy_circuit,
            randomness,
            stack_pointer,
            log_id + 1,
            topics,
            mstart,
            msize,
            is_persistent,
        )
        log_id += is_persistent
        gas_left -= GAS_COST_LOG + GAS_COST_LOG * len(topics) + GAS_COST_LOGDATA * msize

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP,
            rw_counter=rw_dictionary.rw_counter,
            call_id=CALL_ID,
            is_root=False,
            is_create=False,
            code_hash=bytecode_hash,
            program_counter=len(log_entries),
            stack_pointer=stack_pointer,
            memory_size=50,
            gas_left=0,
            log_id=log_id,
        )
    )

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables)
    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )
