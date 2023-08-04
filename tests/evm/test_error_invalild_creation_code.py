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
from zkevm_specs.util.param import INVALID_FIRST_BYTE_CONTRACT_CODE


TESTING_DATA = (
    (0, True),  # is_root
    (0, False),  # not is_root
    (200, True),  # is_root
    (200, False),  # not is_root
)


@pytest.mark.parametrize("offset, is_root", TESTING_DATA)
def test_error_invalid_creation_code(offset: int, is_root: bool):
    bytecode = Bytecode().push32(32).push32(offset).return_()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 1 if is_root else 2
    stack_pointer = 1023
    pc = 66
    reversible_write_counter = 2
    rw_counter = 3 if is_root is True else 15

    # Only need `size` from RETURN opcode
    rw_table = RWDictionary(rw_counter).stack_read(current_call_id, stack_pointer, Word(offset))

    # assign invalid byte `0xEF` to the first byte of memory
    rw_table.memory_read(current_call_id, offset, INVALID_FIRST_BYTE_CONTRACT_CODE)

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
                execution_state=ExecutionState.ErrorInvalidCreationCode,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=is_root,
                is_create=True,
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
                gas_left=0,
                memory_word_size=0,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
