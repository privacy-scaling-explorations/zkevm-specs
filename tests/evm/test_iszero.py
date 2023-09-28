import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import Word


TESTING_DATA = (
    bytes([0]),
    bytes([7]),
)


@pytest.mark.parametrize("value_be_bytes", TESTING_DATA)
def test_iszero(value_be_bytes: bytes):
    value = int.from_bytes(value_be_bytes, "big")
    result = 0x1 if value == 0x0 else 0x0
    value = Word(value)
    result = Word(result)

    bytecode = Bytecode().push1(value_be_bytes).iszero().stop()
    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(RWDictionary(9).stack_read(1, 1023, value).stack_write(1, 1023, result).rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ISZERO,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=2,
                stack_pointer=1023,
                gas_left=3,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=11,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=3,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
