import pytest

from zkevm_specs.evm_circuit import (
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import Word
from zkevm_specs.util.param import MAX_CODE_SIZE


TESTING_DATA = (
    ### insufficient gas case
    # size: 200, gas_left: 40000 - 1,
    (ExecutionState.ErrorOutOfGasCodeStore, 200, 40000 - 1, True),  # is_root
    (ExecutionState.ErrorOutOfGasCodeStore, 200, 40000 - 1, False),  # not is_root
    # size: MAX_CODE_SIZE, gas_left: MAX_CODE_SIZE * 200 - 1
    (
        ExecutionState.ErrorMaxCodeSizeExceeded,
        MAX_CODE_SIZE,
        MAX_CODE_SIZE * 200 - 1,
        True,
    ),  # is_root
    (
        ExecutionState.ErrorMaxCodeSizeExceeded,
        MAX_CODE_SIZE,
        MAX_CODE_SIZE * 200 - 1,
        False,
    ),  # not is_root
    ### bytecode size exceeds MAX_CODE_SIZE
    # size: MAX_CODE_SIZE + 1, gas_left: 5M
    (ExecutionState.ErrorMaxCodeSizeExceeded, MAX_CODE_SIZE + 1, 5 * 10**6, True),  # is_root
    (ExecutionState.ErrorMaxCodeSizeExceeded, MAX_CODE_SIZE + 1, 5 * 10**6, False),  # not is_root
    ### bytecode size exceeds MAX_CODE_SIZE and insufficient gas
    # size: MAX_CODE_SIZE + 1, gas_left: 2M
    (ExecutionState.ErrorMaxCodeSizeExceeded, MAX_CODE_SIZE + 1, 2 * 10**6, True),  # is_root
    (ExecutionState.ErrorMaxCodeSizeExceeded, MAX_CODE_SIZE + 1, 2 * 10**6, False),  # not is_root
)


@pytest.mark.parametrize("execution_state, size, gas_left, is_root", TESTING_DATA)
def test_error_code_store(execution_state: ExecutionState, size: int, gas_left: int, is_root: bool):
    bytecode = Bytecode().push32(size).push32(32).return_()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 1 if is_root else 2
    stack_pointer = 1022
    pc = 66
    reversible_write_counter = 2
    rw_counter = 2 if is_root is True else 14

    # Only need `size` from RETURN opcode
    rw_table = RWDictionary(rw_counter).stack_read(current_call_id, stack_pointer + 1, Word(size))

    # current call context must not be static
    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsStatic, 0)

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    if not is_root:
        # fmt: off
        rw_table \
            .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, True) \
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

    # ErrorOutOfGasCodeStore
    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=execution_state,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=is_root,
                is_create=True,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                memory_word_size=0,
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
                is_root=is_root,
                is_create=True,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                gas_left=gas_left,
                memory_word_size=0,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
