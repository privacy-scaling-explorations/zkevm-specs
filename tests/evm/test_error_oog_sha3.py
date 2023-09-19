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


TESTING_DATA = (
    (32, 32, 41, True),
    (32, 32, 41, False),
    # size is zero, only have GAS_COST_SHA3 cost
    (32, 0, 29, True),
    (32, 0, 29, False),
)


@pytest.mark.parametrize("offset, size, gas_left, is_root", TESTING_DATA)
def test_error_oog_sha3(offset: int, size: int, gas_left: int, is_root: bool):
    bytecode = Bytecode().push(offset).push(size).sha3().stop()
    bytecode_hash = Word(bytecode.hash())

    reversible_write_counter = 2
    current_call_id = 1 if is_root else 2
    rw_counter = 15
    pc = 66
    stack_pointer = 1022
    rw_table = (
        RWDictionary(rw_counter)
        .stack_read(current_call_id, 1022, Word(offset))
        .stack_read(current_call_id, 1023, Word(size))
    )

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    if not is_root:
        # fmt: off
        rw_table \
            .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, is_root) \
            .call_context_read(1, CallContextFieldTag.IsCreate, False) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc + 1) \
            .call_context_read(1, CallContextFieldTag.StackPointer, 1024) \
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
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasSHA3,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                reversible_write_counter=reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                gas_left=0,
            )
            if is_root is True
            else StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                gas_left=gas_left,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
