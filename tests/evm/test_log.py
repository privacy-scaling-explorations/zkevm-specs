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
)
from zkevm_specs.util import rand_address, rand_fp, RLC, U160


TESTING_DATA = (0x030201,)  # rand_address()#
CALLEE_ADDRESS = 0xFF
# TODO: dynamic topic and data generation, so gas will be calculate dynamically.
# TESTING_DATA = (0x030201, topics, data, mstart, msize)
# TESTING_DATA = (0x030201, [0x030201], data, 10, 2)
# TESTING_DATA = (0x030201, [0x030201,0x0f0e0d], data, 10, 100)
# TESTING_DATA = (0x030201, [0x030201,0x0f0e0d, 0x0d8f01], data, 100, 20)
# TESTING_DATA = (0x030201, [0x030201,0x0f0e0d, 0x0d8f01, 0x0aa213],
# data, 1000, 3000)

# topics = [0x030201, 0x0f0e0d, 0x0d8f01,  0x0aa213]


@pytest.mark.parametrize("log", TESTING_DATA)
def test_log(log):
    randomness = rand_fp()
    mstart = 10
    msize = 2
    # for now only test first topic log scenario
    topic1 = 0x030201

    block = Block()

    bytecode = Bytecode().log1()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (1, RW.Read, RWTableTag.Stack, 1, 1020, 0, RLC(mstart, randomness, 8), 0, 0, 0),
                (2, RW.Read, RWTableTag.Stack, 1, 1021, 0, RLC(msize, randomness, 8), 0, 0, 0),
                # write topics
                (3, RW.Read, RWTableTag.Stack, 1, 1022, 0, RLC(topic1, randomness, 32), 0, 0, 0),
                (4, RW.Read, RWTableTag.Memory, 1, 11, 0, 10, 0, 0, 0),
                (5, RW.Read, RWTableTag.Memory, 1, 12, 0, 20, 0, 0, 0),
                # write tx log with topic and data
                (6, RW.Write, RWTableTag.TxLog, 0, 0, TxLogFieldTag.Topics, RLC(topic1, randomness, 32), 0, 0, 0),
                (7, RW.Write, RWTableTag.TxLog, 0, 0, TxLogFieldTag.Data, 10, 0, 0, 0),
                (8, RW.Write, RWTableTag.TxLog, 0, 1, TxLogFieldTag.Data, 20, 0, 0, 0),
                # for contract address
                (
                    9,
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
                (10, RW.Write, RWTableTag.TxLog, 0, 0, TxLogFieldTag.Address, CALLEE_ADDRESS, 0, 0, 0),
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
                stack_pointer=1020,
                gas_left=394,
                state_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=5,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
                state_write_counter=1,
            ),
        ],
    )
