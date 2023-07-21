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

Op = namedtuple(
    "Op",
    ["opcode", "byte_code"],
)


def gen_testing_data():
    opcodes = [
        Op(opcode=Opcode.LOG0, byte_code=Bytecode().log0()),
        Op(opcode=Opcode.LOG1, byte_code=Bytecode().log1()),
        Op(opcode=Opcode.LOG2, byte_code=Bytecode().log2()),
        Op(opcode=Opcode.LOG3, byte_code=Bytecode().log3()),
        Op(opcode=Opcode.LOG4, byte_code=Bytecode().log4()),
        Op(opcode=Opcode.SSTORE, byte_code=Bytecode().sstore()),
        Op(opcode=Opcode.CREATE, byte_code=Bytecode().create()),
        Op(opcode=Opcode.CREATE2, byte_code=Bytecode().create2()),
        Op(opcode=Opcode.CALL, byte_code=Bytecode().call()),
        Op(opcode=Opcode.SELFDESTRUCT, byte_code=Bytecode().selfdestruct()),
    ]
    return [
        (
            opcode.opcode,
            opcode.byte_code,
        )
        for opcode, in product(opcodes)
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize("opcode, bytecode", TESTING_DATA)
def test_error_write_protection(opcode: Opcode, bytecode: Bytecode):
    caller_context = CallContext()
    caller_bytecode_hash = Word(bytecode.hash())

    is_call = opcode is Opcode.CALL

    rw_counter = 17 if is_call is True else 14
    rw_dictionary = RWDictionary(rw_counter).call_context_read(
        2, CallContextFieldTag.IsStatic, FQ(True)
    )

    # Only need to check `value` for CALL op code
    if is_call:
        rw_dictionary.stack_read(2, 1019, Word(100))

    # fmt: off
    rw_dictionary \
        .call_context_read(2, CallContextFieldTag.IsSuccess, 0) \
        .call_context_read(2, CallContextFieldTag.CallerId, 1) \
        .call_context_read(1, CallContextFieldTag.IsRoot, caller_context.is_root) \
        .call_context_read(1, CallContextFieldTag.IsCreate, caller_context.is_create) \
        .call_context_read(1, CallContextFieldTag.CodeHash, caller_bytecode_hash) \
        .call_context_read(1, CallContextFieldTag.ProgramCounter, caller_context.program_counter) \
        .call_context_read(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_read(1, CallContextFieldTag.GasLeft, caller_context.gas_left) \
        .call_context_read(1, CallContextFieldTag.MemorySize, caller_context.memory_word_size) \
        .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, caller_context.reversible_write_counter) \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 2) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorWriteProtection,
                rw_counter=rw_counter,
                call_id=2,
                is_root=False,
                is_create=caller_context.is_create,
                code_hash=caller_bytecode_hash,
                program_counter=0,
                stack_pointer=1017 if is_call is True else 1023,
                gas_left=caller_context.gas_left,
                memory_word_size=caller_context.memory_word_size,
                reversible_write_counter=caller_context.reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dictionary.rw_counter,
                call_id=1,
                is_root=caller_context.is_root,
                is_create=caller_context.is_create,
                code_hash=caller_bytecode_hash,
                program_counter=caller_context.program_counter,
                stack_pointer=caller_context.stack_pointer,
                gas_left=caller_context.gas_left,
                memory_word_size=caller_context.memory_word_size,
                reversible_write_counter=caller_context.reversible_write_counter,
            ),
        ],
    )
