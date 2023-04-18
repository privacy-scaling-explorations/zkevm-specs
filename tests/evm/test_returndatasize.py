import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import Word, U64


TESTING_DATA = (
    0x00,
    0x10,
    0x302010,
)


@pytest.mark.parametrize("returndatasize", TESTING_DATA)
def test_returndatasize(returndatasize: U64):
    bytecode = Bytecode().returndatasize()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(
            RWDictionary(9)
            .call_context_read(1, CallContextFieldTag.LastCalleeReturnDataLength, returndatasize)
            .stack_write(1, 1023, Word(returndatasize))
            .rws
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.RETURNDATASIZE,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=2,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
