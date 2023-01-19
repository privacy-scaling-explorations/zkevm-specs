import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, RLC

TESTING_DATA = ((Opcode.MLOAD, 0, 0),)


@pytest.mark.parametrize("opcode, offset, value", TESTING_DATA)
def test_memory(opcode: Opcode, offset: int, value: int):
    randomness = rand_fq()

    offset = RLC(offset, randomness)
    value = RLC(value, randomness)

    bytecode = Bytecode().mload(offset).stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)
    print(bytecode_hash)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(9).stack_read(1, 1022, offset).stack_write(1, 1022, value).rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.MEMORY,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=6,
                stack_pointer=1021,
                gas_left=8,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=10,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=7,
                stack_pointer=1021,
                gas_left=8,
            ),
        ],
    )
