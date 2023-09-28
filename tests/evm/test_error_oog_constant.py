import pytest

from itertools import chain
from common import CallContext
from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Block,
    Transaction,
    Bytecode,
    RWDictionary,
    Opcode,
)
from zkevm_specs.util import Word


BYTECODE = Bytecode().push1(0x40)
TESTING_DATA_IS_ROOT = ((Transaction(), BYTECODE),)


@pytest.mark.parametrize("tx, bytecode", TESTING_DATA_IS_ROOT)
def test_oog_constant_root(tx: Transaction, bytecode: Bytecode):
    block = Block()

    bytecode_hash = Word(bytecode.hash())

    tables = Tables(
        block_table=set(block.table_assignments()),
        tx_table=set(
            chain(
                tx.table_assignments(),
                Transaction(id=tx.id + 1).table_assignments(),
            )
        ),
        withdrawal_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(RWDictionary(24).call_context_read(1, CallContextFieldTag.IsSuccess, 0).rws),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasConstant,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=2,
                reversible_write_counter=2,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=27,
                call_id=1,
                gas_left=0,
            ),
        ],
    )


TESTING_DATA_NOT_ROOT = ((CallContext(gas_left=10), BYTECODE),)


@pytest.mark.parametrize("caller_ctx, callee_bytecode", TESTING_DATA_NOT_ROOT)
def test_oog_constant_not_root(caller_ctx: CallContext, callee_bytecode: Bytecode):
    caller_bytecode = Bytecode().call(0, 0xFF, 0, 0, 0, 0, 0).stop()
    caller_bytecode_hash = Word(caller_bytecode.hash())
    callee_bytecode_hash = Word(callee_bytecode.hash())
    # gas is insufficient
    callee_gas_left = 2
    callee_reversible_write_counter = 2

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(),
                callee_bytecode.table_assignments(),
            )
        ),
        withdrawal_table=set(),
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
            .call_context_read(1, CallContextFieldTag.MemorySize, caller_ctx.memory_word_size)
            .call_context_read(1, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter)
            .call_context_write(1, CallContextFieldTag.LastCalleeId, 2)
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0)
            .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
            .rws
            # fmt: on
        ),
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasConstant,
                rw_counter=69,
                call_id=2,
                is_root=False,
                is_create=False,
                code_hash=callee_bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=callee_gas_left,
                reversible_write_counter=callee_reversible_write_counter,
                aux_data=Opcode.PUSH1,
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
                memory_word_size=caller_ctx.memory_word_size,
                reversible_write_counter=caller_ctx.reversible_write_counter,
            ),
        ],
    )
