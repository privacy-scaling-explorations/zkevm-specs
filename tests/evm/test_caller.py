import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    CallContextFieldTag,
    Bytecode,
)
from zkevm_specs.util import rand_address, rand_fp, RLC, U160


TESTING_DATA = (0x030201, rand_address())


@pytest.mark.parametrize("caller", TESTING_DATA)
def test_caller(caller: U160):
    randomness = rand_fp()

    bytecode = Bytecode().caller()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (9, RW.Write, RWTableTag.Stack, 1, 1023, RLC(caller, randomness, 20), 0, 0),
                (10, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.CallerAddress, caller, 0, 0),
            ]
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
                code_source=bytecode_hash,
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
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
