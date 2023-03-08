import pytest

from itertools import chain
from collections import namedtuple
from zkevm_specs.util import rand_fq, MAX_MEMORY_SIZE, RLC
from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    CallContextFieldTag,
    Block,
    Account,
    AccountFieldTag,
    Transaction,
    Bytecode,
    RWDictionary,
)

CallContext = namedtuple(
    "CallContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_word_size",
        "reversible_write_counter",
    ],
    defaults=[True, False, 232, 1023, 0, 0, 0],
)


Stack = namedtuple(
    "Stack",
    ["gas", "value", "cd_offset", "cd_length", "rd_offset", "rd_length"],
    defaults=[100, 0, 64, 320, 0, 32],
)


TEST_DATA = [
    (
        CallContext(memory_word_size=MAX_MEMORY_SIZE + 1),
        Transaction(
            call_data=bytes.fromhex(
                "00000000000000000000000000000000000000000000000000000000000000FF"
            )
        ),
        Stack(),
        Account(address=0xFF, code=Bytecode().stop(), balance=int(1e18)),
    )
]


@pytest.mark.parametrize("ctx, tx, stack, account", TEST_DATA)
def test_error_gas_uint_overflow_root(
    ctx: CallContext, tx: Transaction, stack: Stack, account: Account
):
    randomness = rand_fq()

    bytecode = Bytecode().add()
    bytecode_hash = RLC(bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(account.code_hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(24)
            .call_context_read(1, CallContextFieldTag.MemorySize, ctx.memory_word_size)
            .call_context_read(1, CallContextFieldTag.TxId, tx.id)
            .stack_read(1, 1017, RLC(stack.gas, randomness))
            .stack_read(1, 1018, RLC(account.address, randomness))
            .stack_read(1, 1019, RLC(stack.value, randomness))
            .stack_read(1, 1020, RLC(stack.cd_offset, randomness))
            .stack_read(1, 1021, RLC(stack.cd_length, randomness))
            .stack_read(1, 1022, RLC(stack.rd_offset, randomness))
            .stack_read(1, 1023, RLC(stack.rd_length, randomness))
            .stack_write(1, 1023, RLC(False, randomness))
            .account_read(account.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
            .tx_access_list_account_read(1, account.address, True)
            .call_context_read(1, CallContextFieldTag.CallDataOffset, 0)
            .call_context_read(1, CallContextFieldTag.CallDataLength, len(tx.call_data))
            .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorGasUintOverflow,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1017,
                gas_left=3,
                reversible_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=36,
                call_id=1,
                gas_left=0,
            ),
        ],
    )


@pytest.mark.parametrize("ctx, tx, stack, account", TEST_DATA)
def test_error_gas_uint_overflow_not_root(
    ctx: CallContext, tx: Transaction, stack: Stack, account: Account
):
    randomness = rand_fq()

    caller_id = 1
    callee_id = 2
    caller_bytecode = Bytecode().call(0, 0xFF, 0, 0, 0, 0, 0).stop()
    callee_bytecode = Bytecode().add().stop()
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(callee_bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(tx.table_assignments(randomness)),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee_bytecode.table_assignments(randomness),
            )
        ),
        rw_table=set(
            RWDictionary(24)
            .call_context_read(callee_id, CallContextFieldTag.MemorySize, ctx.memory_word_size)
            .call_context_read(callee_id, CallContextFieldTag.TxId, tx.id)
            .stack_read(callee_id, 1017, RLC(stack.gas, randomness))
            .stack_read(callee_id, 1018, RLC(account.address, randomness))
            .stack_read(callee_id, 1019, RLC(stack.value, randomness))
            .stack_read(callee_id, 1020, RLC(stack.cd_offset, randomness))
            .stack_read(callee_id, 1021, RLC(stack.cd_length, randomness))
            .stack_read(callee_id, 1022, RLC(stack.rd_offset, randomness))
            .stack_read(callee_id, 1023, RLC(stack.rd_length, randomness))
            .stack_write(callee_id, 1023, RLC(False, randomness))
            .account_read(account.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
            .tx_access_list_account_read(caller_id, account.address, True)
            .call_context_read(callee_id, CallContextFieldTag.CallDataOffset, 0)
            .call_context_read(callee_id, CallContextFieldTag.CallDataLength, len(tx.call_data))
            .call_context_read(callee_id, CallContextFieldTag.IsSuccess, 0)
            .call_context_read(callee_id, CallContextFieldTag.CallerId, caller_id)
            .call_context_read(caller_id, CallContextFieldTag.IsRoot, ctx.is_root)
            .call_context_read(caller_id, CallContextFieldTag.IsCreate, ctx.is_create)
            .call_context_read(caller_id, CallContextFieldTag.CodeHash, caller_bytecode_hash)
            .call_context_read(caller_id, CallContextFieldTag.ProgramCounter, ctx.program_counter)
            .call_context_read(caller_id, CallContextFieldTag.StackPointer, ctx.stack_pointer)
            .call_context_read(caller_id, CallContextFieldTag.GasLeft, ctx.gas_left)
            .call_context_read(caller_id, CallContextFieldTag.MemorySize, ctx.memory_word_size)
            .call_context_read(
                caller_id, CallContextFieldTag.ReversibleWriteCounter, ctx.reversible_write_counter
            )
            .call_context_write(caller_id, CallContextFieldTag.LastCalleeId, callee_id)
            .call_context_write(caller_id, CallContextFieldTag.LastCalleeReturnDataOffset, 0)
            .call_context_write(caller_id, CallContextFieldTag.LastCalleeReturnDataLength, 0)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorGasUintOverflow,
                rw_counter=24,
                call_id=callee_id,
                is_root=False,
                is_create=False,
                code_hash=callee_bytecode_hash,
                program_counter=0,
                stack_pointer=1017,
                gas_left=ctx.gas_left,
                reversible_write_counter=0,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=48,
                call_id=caller_id,
                is_root=ctx.is_root,
                is_create=ctx.is_create,
                code_hash=caller_bytecode_hash,
                program_counter=ctx.program_counter,
                stack_pointer=ctx.stack_pointer,
                gas_left=ctx.gas_left,
                memory_word_size=ctx.memory_word_size,
                reversible_write_counter=ctx.reversible_write_counter,
            ),
        ],
    )
