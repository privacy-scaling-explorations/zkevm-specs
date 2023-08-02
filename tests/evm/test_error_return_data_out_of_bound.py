import pytest

from zkevm_specs.util import Word
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
from zkevm_specs.util.param import MAX_U64


TESTING_DATA = (
    ## is_root is True
    # is_data_offset_u64_overflow is True
    (MAX_U64 + 1, 0, True),
    # is_end_u64_overflow is True
    (MAX_U64, 1, True),
    (1, MAX_U64, True),
    (0, MAX_U64 + 1, True),
    # is_end_over_return_data_len is True (as we set return_data_length to 320)
    (321, 0, True),
    (320, 1, True),
    ## Same cases, with is_root set to False
    (MAX_U64 + 1, 0, False),
    (MAX_U64, 1, False),
    (1, MAX_U64, False),
    (0, MAX_U64 + 1, False),
    (321, 0, False),
    (320, 1, False),
)


@pytest.mark.parametrize("data_offset, length, is_root", TESTING_DATA)
def test_error_return_data_out_of_bound(
    data_offset: int,
    length: int,
    is_root: bool,
):
    bytecode = Bytecode().push32(32).push32(data_offset).push32(length).returndatacopy()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 1 if is_root else 2
    stack_pointer = 1021
    pc = 99
    reversible_write_counter = 2
    rw_counter = 4 if is_root is True else 16

    # Only need `size` from RETURN opcode
    rw_table = (
        RWDictionary(rw_counter)
        .stack_read(current_call_id, stack_pointer + 1, Word(data_offset))
        .stack_read(current_call_id, stack_pointer + 2, Word(length))
    )

    rw_table.call_context_read(current_call_id, CallContextFieldTag.LastCalleeReturnDataLength, 320)

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    if not is_root:
        # fmt: off
        rw_table \
            .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, False) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc + 1) \
            .call_context_read(1, CallContextFieldTag.StackPointer, 1024) \
            .call_context_read(1, CallContextFieldTag.GasLeft, 0) \
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
                execution_state=ExecutionState.ErrorReturnDataOutOfBound,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=100,
                memory_word_size=0,
                reversible_write_counter=reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
            )
            if is_root is True
            else StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter + reversible_write_counter,
                call_id=1,
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                gas_left=0,
                memory_word_size=0,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
