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
    (Opcode.LOG0, 32, 32, 636),
    (Opcode.LOG1, 32, 32, 1011),
    (Opcode.LOG2, 32, 32, 1386),
    (Opcode.LOG3, 32, 32, 1761),
    (Opcode.LOG4, 32, 32, 2136),
)


@pytest.mark.parametrize("opcode, offset, size, gas_left", TESTING_DATA)
def test_error_oog_log(opcode: Opcode, offset: int, size: int, gas_left: int):
    if opcode == Opcode.LOG0:
        bytecode = Bytecode().log0()
    elif opcode == Opcode.LOG1:
        bytecode = Bytecode().log1()
    elif opcode == Opcode.LOG2:
        bytecode = Bytecode().log2()
    elif opcode == Opcode.LOG3:
        bytecode = Bytecode().log3()
    else:
        bytecode = Bytecode().log4()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 2
    rw_counter = 14
    rw_table = (
        RWDictionary(rw_counter)
        .stack_read(current_call_id, 1022, Word(offset))
        .stack_read(current_call_id, 1023, Word(size))
    )
    stack_pointer = 1022
    pc = (Opcode.LOG4 - Opcode.LOG0 + 1) * 33 + 1

    memory_word_size = 0 if size == 0 else (offset + size + 31) // 32

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    # fmt: off
    rw_table \
        .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
        .call_context_read(1, CallContextFieldTag.IsRoot, False) \
        .call_context_read(1, CallContextFieldTag.IsCreate, False) \
        .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash) \
        .call_context_read(1, CallContextFieldTag.ProgramCounter, pc) \
        .call_context_read(1, CallContextFieldTag.StackPointer, stack_pointer) \
        .call_context_read(1, CallContextFieldTag.GasLeft, gas_left) \
        .call_context_read(1, CallContextFieldTag.MemorySize, memory_word_size) \
        .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, 0) \
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
                execution_state=ExecutionState.ErrorOutOfGasLOG,
                rw_counter=rw_counter,
                call_id=current_call_id,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                reversible_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_table.rw_counter,
                call_id=1,
                is_root=False,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc,
                stack_pointer=stack_pointer,
                gas_left=gas_left,
                memory_word_size=memory_word_size,
                reversible_write_counter=0,
            ),
        ],
    )
