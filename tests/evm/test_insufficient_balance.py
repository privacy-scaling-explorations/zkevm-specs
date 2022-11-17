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
    AccountFieldTag,
)
from zkevm_specs.util import rand_fq, RLC
from itertools import chain
from collections import namedtuple


TESTING_DATA = (
    # balance | transfer value
    (200, 250),
    (1, 2),
)


@pytest.mark.parametrize("balance, transfer_value", TESTING_DATA)
def test_insufficient_balance_root(balance: int, transfer_value: int):
    randomness = rand_fq()

    block = Block()
    bytecode = Bytecode().call(0, 0xFC, transfer_value, 0, 0, 0, 0).stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    tables = Tables(
        block_table=set(block.table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(
            RWDictionary(9)
            .stack_read(1, 1010, RLC(10000, randomness))  # gas
            .stack_read(1, 1011, RLC(0xFC, randomness))  # address
            .stack_read(1, 1012, RLC(transfer_value, randomness))  # value
            .call_context_read(1, CallContextFieldTag.CalleeAddress, 0xFE)
            .account_read(0xFE, AccountFieldTag.Balance, RLC(balance, randomness))
            .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
            .rws
        ),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorInsufficientBalance,
                rw_counter=9,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=231,
                stack_pointer=1010,
                gas_left=8,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=15,
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

TESTING_DATA_NOT_ROOT = ((CallContext(), 100, 101),)


@pytest.mark.parametrize("caller_ctx, balance, transfer_value", TESTING_DATA_NOT_ROOT)
def test_insufficient_balance_not_root(caller_ctx: CallContext, balance: int, transfer_value: int):
    randomness = rand_fq()

    caller_bytecode = Bytecode().call(0, 0xFF, 0, 0, 0, 0, 0).stop()
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode = Bytecode().call(0, 0xFC, transfer_value, 0, 0, 0, 0).stop()
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
            .stack_read(2, 1010, RLC(10000, randomness))  # gas
            .stack_read(2, 1011, RLC(0xfc, randomness))  # address
            .stack_read(2, 1012, RLC(transfer_value, randomness))  # value
            .call_context_read(2, CallContextFieldTag.CalleeAddress, 0xfe)
            .account_read(0xfe, AccountFieldTag.Balance, RLC(balance, randomness))
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
                execution_state=ExecutionState.ErrorInsufficientBalance,
                rw_counter=69,
                call_id=2,
                is_root=False,
                is_create=False,
                code_hash=callee_bytecode_hash,
                program_counter=231,
                stack_pointer=1010,
                gas_left=10,
                reversible_write_counter=callee_reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=87,
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
