import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    Block,
    Bytecode,
)
from zkevm_specs.util import  rand_fq, RLC, U256
from zkevm_specs.util.param import N_BYTES_WORD


TESTING_DATA = (0x030201, rand_fq())


@pytest.mark.parametrize("chainid", TESTING_DATA)
def test_chainid(chainid: U256):
    randomness = rand_fq()

    block = Block(chainid=chainid)

    bytecode = Bytecode().chainid()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (9, RW.Write, RWTableTag.Stack, 1, 1023, 0, RLC(chainid, randomness, N_BYTES_WORD), 0, 0, 0),
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CHAINID,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=10,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
