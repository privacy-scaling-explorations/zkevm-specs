import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    TxLogFieldTag,
    CallContextFieldTag,
    RW,
    Block,
    Bytecode,
    LOG_STATIC_GAS,
)
from zkevm_specs.util import rand_range, rand_address, rand_fp, RLC, U64, U256, memory_expansion

# TESTING_DATA = (topics, mstart, msize)
TESTING_DATA = (
    # zero topic
    ([], 10, 2),
    # one topic
    ([0x030201], 20, 3),
    # two topics
    ([0x030201, 0x0F0E0D], 100, 20),
    # four topics
    ([0x030201, 0x0F0E0D, 0x0D8F01, 0x0AA213], 421, 15),
)
CALLEE_ADDRESS = rand_address()

bytecodes = [Bytecode().log0(), Bytecode().log1(), Bytecode().log2(), Bytecode().log3(), Bytecode().log4()]


@pytest.mark.parametrize("topics, mstart, msize", TESTING_DATA)
def test_log(topics: list, mstart: U64, msize: U64):
    randomness = rand_fp()
    block = Block()

    data = []
    for i in range(msize):
        data.append(rand_range(255))

    topic_count = len(topics)
    next_memory_size, memory_expansion_cost = memory_expansion(mstart, msize)
    dynamic_gas = LOG_STATIC_GAS * topic_count + 8 * msize + memory_expansion_cost

    bytecode = bytecodes[topic_count]
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (1, RW.Read, RWTableTag.Stack, 1, 1017, 0, RLC(mstart, randomness, 8), 0, 0, 0),
                (2, RW.Read, RWTableTag.Stack, 1, 1018, 0, RLC(msize, randomness, 8), 0, 0, 0),
            ]  # write topics
            + construct_topic_stack(3, 1019, topics, randomness)
            + construct_memory_rows(3 + topic_count, data, mstart, randomness)
            + construct_topic_rows(3 + topic_count + msize, topics, randomness)
            + construct_data_rows(3 + 2 * topic_count + msize, data, randomness)
            + [
                # demo rows of one topic with two data
                # (3, RW.Read, RWTableTag.Stack, 1, 1022, 0, RLC(topic1, randomness, 32), 0, 0, 0),
                # (4, RW.Read, RWTableTag.Memory, 1, 11, 0, 10, 0, 0, 0),
                # (5, RW.Read, RWTableTag.Memory, 1, 12, 0, 20, 0, 0, 0),
                # write tx log with topic and data
                # (6, RW.Write, RWTableTag.TxLog, 0, 0, TxLogFieldTag.Topics, RLC(topic1, randomness, 32), 0, 0, 0),
                # (7, RW.Write, RWTableTag.TxLog, 0, 0, TxLogFieldTag.Data, 10, 0, 0, 0),
                # (8, RW.Write, RWTableTag.TxLog, 0, 1, TxLogFieldTag.Data, 20, 0, 0, 0),
                # for not static call
                (
                    3 + 2 * topic_count + 2 * msize,
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
                # for contract address
                (
                    4 + 2 * topic_count + 2 * msize,
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
                    5 + 2 * topic_count + 2 * msize,
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
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.LOG,
                rw_counter=1,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1017,
                gas_left=2000,
                state_write_counter=0,
                memory_size=mstart,
                log_index=0,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=6 + 2 * topic_count + 2 * msize,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1019 + topic_count,
                gas_left=2000 - dynamic_gas,
                state_write_counter=1,
                memory_size=next_memory_size,
                log_index=1,
            ),
        ],
    )


# helper to construct topics or data rows of RW table
def construct_topic_rows(gc: U256, topics: list, randomness: int):
    rows = []
    i = 0
    for topic in topics:
        rows.append((gc, RW.Write, RWTableTag.TxLog, 0, i, TxLogFieldTag.Topics, RLC(topic, randomness, 32), 0, 0, 0))
        gc += 1
        i += 1
    return rows


def construct_topic_stack(gc: U256, sp: int, topics: list, randomness: int):
    rows = []
    for topic in topics:
        rows.append((gc, RW.Read, RWTableTag.Stack, 1, sp, 0, RLC(topic, randomness, 32), 0, 0, 0))
        sp += 1
        gc += 1
    return rows


def construct_data_rows(gc: U256, data: list, randomness: int):
    rows = []
    i = 0
    for byte in data:
        rows.append((gc, RW.Write, RWTableTag.TxLog, 0, i, TxLogFieldTag.Data, RLC(byte, randomness, 32), 0, 0, 0))
        gc += 1
        i += 1
    return rows


def construct_memory_rows(gc: U256, data: list, mstart: U64, randomness: int):
    rows = []
    i = 1
    for byte in data:
        rows.append((gc, RW.Read, RWTableTag.Memory, 1, mstart + i, 0, byte, 0, 0, 0))
        i += 1
        gc += 1
    return rows
