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
    Opcode,
)
from zkevm_specs.util import Word


TESTING_DATA = (
    (Opcode.MLOAD, 32, False, 8),
    (Opcode.MLOAD, 32, True, 8),
    (Opcode.MSTORE, 32, False, 8),
    (Opcode.MSTORE, 32, True, 8),
    (Opcode.MSTORE8, 32, False, 8),
    (Opcode.MSTORE8, 32, True, 8),
)


@pytest.mark.parametrize("opcode, offset, is_root, gas_left", TESTING_DATA)
def test_error_oog_static_memory_expansion(
    opcode: Opcode, offset: int, is_root: bool, gas_left: int
):
    if opcode == Opcode.MLOAD:
        bytecode = Bytecode().push32(offset).mload().stop()
    elif opcode == Opcode.MSTORE:
        bytecode = Bytecode().push32(offset).mstore().stop()
    else:
        bytecode = Bytecode().push8(offset).mstore8().stop()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 1 if is_root else 2
    rw_counter = 14
    stack_pointer = 1023
    reversible_write_counter = 2

    rw_table = RWDictionary(rw_counter).stack_read(current_call_id, stack_pointer, Word(offset))

    if opcode == Opcode.MSTORE8:
        pc = 9
        size = 8
    else:
        pc = 33
        size = 32

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    if not is_root:
        memory_word_size = 1 if size == 0 else (offset + size + 31) // 32
        # fmt: off
        rw_table \
            .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, False) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc + 1) \
            .call_context_read(1, CallContextFieldTag.StackPointer, 1024) \
            .call_context_read(1, CallContextFieldTag.GasLeft, gas_left) \
            .call_context_read(1, CallContextFieldTag.MemorySize, memory_word_size) \
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
                execution_state=ExecutionState.ErrorOutOfGasStaticMemoryExpansion,
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
                is_root=is_root,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc + 1,
                stack_pointer=1024,
                gas_left=gas_left,
                memory_word_size=memory_word_size,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
