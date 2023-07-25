from collections import namedtuple
from itertools import product

import pytest
from common import CallContext

from zkevm_specs.evm_circuit import (
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.util import Word
from zkevm_specs.util.arithmetic import FQ
from zkevm_specs.util.param import MAX_CODE_SIZE

Op = namedtuple(
    "Op",
    ["opcode", "byte_code"],
)


def gen_testing_data():
    size = [10, MAX_CODE_SIZE, MAX_CODE_SIZE + 1]
    is_root = [True, False]
    gas_left = [10]
    return [
        (size, is_root, gas_left) for size, is_root, gas_left in product(size, is_root, gas_left)
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize("size, is_root, gas_left", TESTING_DATA)
def test_error_code_store(size: int, is_root: bool, gas_left: int):
    bytecode = Bytecode().push32(size).push32(32).return_()
    bytecode_hash = Word(bytecode.hash())

    current_call_id = 1 if is_root else 2
    stack_pointer = 1022
    pc = 66
    reversible_write_counter = 2
    rw_counter = 2 if is_root is True else 14

    # Only need `size` from RETURN opcode
    rw_table = RWDictionary(rw_counter).stack_read(current_call_id, stack_pointer + 1, Word(size))

    rw_table.call_context_read(current_call_id, CallContextFieldTag.IsSuccess, 0)

    if not is_root:
        # fmt: off
        rw_table \
            .call_context_read(current_call_id, CallContextFieldTag.CallerId, 1) \
            .call_context_read(1, CallContextFieldTag.IsRoot, is_root) \
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
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_table.rws),
    )

    # ErrorOutOfGasCodeStore
    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorMaxCodeSizeExceeded,
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
