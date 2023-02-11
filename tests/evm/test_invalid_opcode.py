import pytest
from collections import namedtuple
from itertools import chain
from zkevm_specs.evm import (
    Block,
    Bytecode,
    CallContextFieldTag,
    ExecutionState,
    RWDictionary,
    StepState,
    Tables,
    Transaction,
    verify_steps,
)
from zkevm_specs.util import RLC, rand_fq

TESTING_INVALID_CODES = [
    # Single invalid opcode
    [0x0E],
    [0x1F],
    [0x21],
    [0x4F],
    [0xA5],
    [0xB0],
    [0xC0],
    [0xD0],
    [0xE0],
    [0xF6],
    [0xFB],
    [0xFE],
    # Multiple invalid opcodes
    [0x5C, 0x5D, 0x5E, 0x5F],
    # Many duplicate invalid opcodes
    [0x22] * 256,
]


@pytest.mark.parametrize("invalid_code", TESTING_INVALID_CODES)
def test_invalid_opcode_root(invalid_code):
    randomness = rand_fq()

    bytecode = Bytecode(bytearray(invalid_code), [True] * len(invalid_code)).stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    block = Block()
    tx = Transaction()

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(
            chain(
                tx.table_assignments(randomness),
                Transaction(id=tx.id + 1).table_assignments(randomness),
            )
        ),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(RWDictionary(24).call_context_read(1, CallContextFieldTag.IsSuccess, 0).rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorInvalidOpcode,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=2,
                reversible_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=25,
                call_id=1,
                gas_left=0,
            ),
        ],
    )


CallContext = namedtuple(
    "CallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[True, False, 232, 1023, 10, 0, 0],
)


@pytest.mark.parametrize("invalid_callee_code", TESTING_INVALID_CODES)
def test_invalid_opcode_internal(invalid_callee_code: list[int]):
    randomness = rand_fq()

    caller_ctx = CallContext()
    caller_bytecode = Bytecode().call(0, 0xFF, 0, 0, 0, 0, 0).stop()
    callee_bytecode = Bytecode(
        bytearray(invalid_callee_code), [True] * len(invalid_callee_code)
    ).stop()
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(callee_bytecode.hash(), randomness)

    callee_reversible_write_counter = 2

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee_bytecode.table_assignments(randomness),
            )
        ),
        rw_table=set(
            # fmt: off
            RWDictionary(69)
            .call_context_read(2, CallContextFieldTag.IsSuccess, 0)
            .call_context_read(2, CallContextFieldTag.CallerId, 1)
            .call_context_read(1, CallContextFieldTag.IsRoot, caller_ctx.is_root)
            .call_context_read(1, CallContextFieldTag.IsCreate, caller_ctx.is_create)
            .call_context_read(1, CallContextFieldTag.CodeHash, caller_bytecode_hash)
            .call_context_read(1, CallContextFieldTag.ProgramCounter, caller_ctx.program_counter)
            .call_context_read(1, CallContextFieldTag.StackPointer, caller_ctx.stack_pointer)
            .call_context_read(1, CallContextFieldTag.GasLeft, caller_ctx.gas_left)
            .call_context_read(1, CallContextFieldTag.MemorySize, caller_ctx.memory_size)
            .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter)
            .call_context_write(1, CallContextFieldTag.LastCalleeId, 2)
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0)
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
            .rws
            # fmt: on
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorInvalidOpcode,
                rw_counter=69,
                call_id=2,
                is_root=False,
                is_create=False,
                code_hash=callee_bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=10,
                reversible_write_counter=callee_reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=82 + callee_reversible_write_counter,
                call_id=1,
                is_root=caller_ctx.is_root,
                is_create=caller_ctx.is_create,
                code_hash=caller_bytecode_hash,
                program_counter=caller_ctx.program_counter,
                stack_pointer=caller_ctx.stack_pointer,
                gas_left=caller_ctx.gas_left,
                memory_size=caller_ctx.memory_size,
                reversible_write_counter=caller_ctx.reversible_write_counter,
            ),
        ],
    )
