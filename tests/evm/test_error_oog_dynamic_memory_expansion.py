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


TESTING_DATA_IS_ROOT = (
    (True, Opcode.RETURN, 32, 32, 5),
    (True, Opcode.REVERT, 32, 32, 5),
    (True, Opcode.CREATE, 32, 32, 32001),
    (True, Opcode.CREATE2, 32, 32, 32001),
    (False, Opcode.RETURN, 32, 32, 5),
    (False, Opcode.REVERT, 32, 32, 5),
    (False, Opcode.CREATE, 32, 32, 32001),
    (False, Opcode.CREATE2, 32, 32, 32001),
)


@pytest.mark.parametrize("is_root, opcode, offset, length, gas_left", TESTING_DATA_IS_ROOT)
def test_oog_dynamic_memory_expansion_root(
    is_root: bool, opcode: Opcode, offset: int, length: int, gas_left: int
):
    # It's a cumulative reversible write counter and it'll be 2 after BeginTx
    # It could a random value as well but
    # we can verify the rw_counter in the next call context is correct or not.
    # So, it's better to be a non-zero value
    reversible_write_counter = 2

    rw_counter = 2 if is_root else 14
    caller_id = 1 if is_root else 2
    is_create = True if opcode == Opcode.CREATE or opcode == Opcode.CREATE2 else False
    if is_create:
        stack_pointer = 1020
        bytecode = Bytecode().create()
        rw_table = (
            RWDictionary(rw_counter)
            .stack_read(caller_id, stack_pointer + 1, Word(offset))
            .stack_read(caller_id, stack_pointer + 2, Word(length))
        )
        pc = 100
    else:
        stack_pointer = 1021
        bytecode = Bytecode().return_() if opcode == Opcode.RETURN else Bytecode().revert()
        rw_table = (
            RWDictionary(rw_counter - 1)
            .stack_read(caller_id, stack_pointer, Word(offset))
            .stack_read(caller_id, stack_pointer + 1, Word(length))
        )
        pc = 67

    bytecode_hash = Word(bytecode.hash())

    rw_table.call_context_read(caller_id, CallContextFieldTag.IsSuccess, 0)

    # fmt: off
    if not is_root:
        memory_word_size = (
            0 if length == 0 else (offset + length + 31) // 32
        )
        rw_table \
            .call_context_read(2, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, False) \
            .call_context_read(1, CallContextFieldTag.IsCreate, is_create) \
            .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
            .call_context_read(1, CallContextFieldTag.ProgramCounter, pc) \
            .call_context_read(1, CallContextFieldTag.StackPointer, stack_pointer) \
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
                execution_state=ExecutionState.ErrorOutOfGasDynamicMemoryExpansion,
                rw_counter=rw_counter if is_create else rw_counter - 1,
                call_id=caller_id,
                is_root=is_root,
                is_create=is_create,
                code_hash=bytecode_hash,
                program_counter=0,
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
                is_create=is_create,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                memory_word_size=memory_word_size,
                reversible_write_counter=reversible_write_counter,
            ),
        ],
    )
