import pytest

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Block,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import Word


POW2 = 2**256
TESTING_DATA = (
    (0, 9),
    (10, 59),
    (POW2 - 1, 1609),
)


@pytest.mark.parametrize("exponent, gas_left", TESTING_DATA)
def test_error_oog_exp(exponent: int, gas_left: int):
    bytecode = Bytecode().exp()
    bytecode_hash = Word(bytecode.hash())

    reversible_write_counter = 2
    current_call_id = 2
    rw_counter = 13
    pc = 1 * 33 + 1
    stack_pointer = 1022
    rw_table = RWDictionary(rw_counter).stack_read(
        current_call_id, stack_pointer + 1, Word(exponent)
    )

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    # fmt: off
    rw_table \
        .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
        .call_context_read(1, CallContextFieldTag.IsRoot, False) \
        .call_context_read(1, CallContextFieldTag.IsCreate, False) \
        .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
        .call_context_read(1, CallContextFieldTag.ProgramCounter, pc) \
        .call_context_read(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_read(1, CallContextFieldTag.GasLeft, gas_left) \
        .call_context_read(1, CallContextFieldTag.MemorySize, 0) \
        .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, reversible_write_counter) \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasEXP,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                reversible_write_counter=reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=1023,
                gas_left=gas_left,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
