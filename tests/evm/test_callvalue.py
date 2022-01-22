import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    CallContextFieldTag,
    Bytecode,
)
from zkevm_specs.util import rand_fp, RLC, U256
from zkevm_specs.util.param import N_BYTES_WORD


TESTING_DATA = (
    0x00,
    0x10,
    0x302010,
    0xF0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0F,
)


@pytest.mark.parametrize("callvalue", TESTING_DATA)
def test_callvalue(callvalue: U256):
    randomness = rand_fp()

    callvalue_rlc = RLC(callvalue, randomness, N_BYTES_WORD)

    bytecode = Bytecode().callvalue()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            [
                (9, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.Value, callvalue_rlc, 0, 0),
                (10, RW.Write, RWTableTag.Stack, 1, 1023, callvalue_rlc, 0, 0),
            ]
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CALLVALUE,
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
