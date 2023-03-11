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
from zkevm_specs.util import RLC, U160
from common import rand_fq, rand_address


TESTING_DATA = (
    0x00,
    0x10,
    0x030201,
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    rand_address(),
)


@pytest.mark.parametrize("caller", TESTING_DATA)
def test_caller(caller: U160):
    randomness = rand_fq()

    bytecode = Bytecode().caller()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .call_context_read(1, CallContextFieldTag.CallerAddress, caller)
            .stack_write(1, 1023, RLC(caller, randomness))
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CALLER,
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
