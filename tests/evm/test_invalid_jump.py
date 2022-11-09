import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    Opcode,
    verify_steps,
    Tables,
    Block,
    Bytecode,
    RWDictionary,
    CallContextFieldTag,
)
from zkevm_specs.util import rand_fq, RLC
from itertools import chain
from collections import namedtuple


TESTING_DATA = (
    (Opcode.JUMP, bytes([5])),
    # out of range
    (Opcode.JUMP, bytes([20])),
)


@pytest.mark.parametrize("opcode, dest_bytes", TESTING_DATA)
def test_invalid_jump_root(opcode: Opcode, dest_bytes: bytes):
    randomness = rand_fq()
    dest = RLC(bytes(reversed(dest_bytes)), randomness)

    block = Block()
    # dest is invalid for error case
    # PUSH1 80 PUSH1 40 PUSH1 07 JUMP JUMPDEST STOP
    bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jump().jumpdest().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1021, dest)
            .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorInvalidJump,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=6,
                stack_pointer=1021,
                gas_left=8,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=11,
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

TESTING_DATA_NOT_ROOT = (
    (CallContext(), bytes([5])),
    (CallContext(), bytes([20])),
)


@pytest.mark.parametrize("caller_ctx, dest_bytes", TESTING_DATA_NOT_ROOT)
def test_invalid_jump_not_root(caller_ctx: CallContext, dest_bytes: bytes):
    randomness = rand_fq()
    dest = RLC(bytes(reversed(dest_bytes)), randomness)

    caller_bytecode = Bytecode().call(0, 0xFF, 0, 0, 0, 0, 0).stop()
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode = Bytecode().push1(0x80).push1(0x40).push1(dest_bytes).jump().jumpdest().stop()
    callee_bytecode_hash = RLC(callee_bytecode.hash(), randomness)
    callee_reversible_write_counter = 0

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
            .stack_read(2, 1021, dest)
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
                execution_state=ExecutionState.ErrorInvalidJump,
                rw_counter=69,
                call_id=2,
                is_root=False,
                is_create=False,
                code_hash=callee_bytecode_hash,
                program_counter=6,
                stack_pointer=1021,
                gas_left=10,
                reversible_write_counter=callee_reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=83,
                call_id=1,
                is_root=caller_ctx.is_root,
                is_create=caller_ctx.is_create,
                code_hash=caller_bytecode_hash,
                program_counter=caller_ctx.program_counter,
                stack_pointer=caller_ctx.stack_pointer,
                gas_left=caller_ctx.gas_left,
                memory_size=caller_ctx.memory_size,
                reversible_write_counter=caller_ctx.reversible_write_counter
                + callee_reversible_write_counter,
            ),
        ],
    )
