import itertools
import pytest
from collections import namedtuple
from itertools import chain

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    AccountFieldTag,
    CallContextFieldTag,
    Block,
    Account,
    Bytecode,
    RWDictionary,
)
from zkevm_specs.util import rand_fq, RLC, EMPTY_CODE_HASH
from zkevm_specs.util.param import (
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_WARM_ACCESS,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_STIPEND_CALL_WITH_VALUE,
)


CallContext = namedtuple(
    "CallContext",
    [
        "rw_counter_end_of_reversion",
        "is_persistent",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[0, False, 0, 0, 2],
)
Stack = namedtuple(
    "Stack",
    ["gas", "value", "cd_offset", "cd_length", "rd_offset", "rd_length"],
    defaults=[0, 0, 0, 0, 0, 0],
)

STOP_BYTECODE = Bytecode().stop()

CALLER = Account(address=0xFE, balance=int(1e20))
CALLEE_WITH_STOP_BYTECODE_AND_BALANCE = Account(address=0xFF, code=STOP_BYTECODE, balance=int(1e18))


def gen_testing_data():
    callees = [
        CALLEE_WITH_STOP_BYTECODE_AND_BALANCE,
    ]
    call_contexts = [
        CallContext(gas_left=50, is_persistent=False),
        CallContext(gas_left=100, is_persistent=False, rw_counter_end_of_reversion=0),
    ]
    stacks = [
        Stack(gas=100, cd_offset=64, cd_length=320, rd_offset=0, rd_length=32),
    ]
    is_warm_accesss = [True, False]

    return [
        (
            CALLER,
            callee,
            call_context,
            stack,
            is_warm_access,
        )
        for callee, call_context, stack, is_warm_access in itertools.product(
            callees, call_contexts, stacks, is_warm_accesss
        )
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize("caller, callee, caller_ctx, stack, is_warm_access", TESTING_DATA)
def test_root_call(
    caller: Account,
    callee: Account,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
):
    randomness = rand_fq()

    callee_balance = RLC(callee.balance + stack.value, randomness)
    caller_bytecode = (
        Bytecode()
        .call(
            stack.gas,
            callee.address,
            stack.value,
            stack.cd_offset,
            stack.cd_length,
            stack.rd_offset,
            stack.rd_length,
        )
        .stop()
    )
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(callee.code_hash(), randomness)

    is_success = False

    # fmt: off
    rw_dictionary = (
        RWDictionary(24)
        .call_context_read(1, CallContextFieldTag.TxId, 1)
        .call_context_read(1, CallContextFieldTag.IsStatic, False)
        .stack_read(1, 1017, RLC(stack.gas, randomness))
        .stack_read(1, 1018, RLC(callee.address, randomness))
        .stack_read(1, 1019, RLC(stack.value, randomness))
        .stack_read(1, 1020, RLC(stack.cd_offset, randomness))
        .stack_read(1, 1021, RLC(stack.cd_length, randomness))
        .stack_read(1, 1022, RLC(stack.rd_offset, randomness))
        .stack_read(1, 1023, RLC(stack.rd_length, randomness))
        .stack_write(1, 1023, RLC(is_success, randomness))
        .tx_access_list_account_read(1, callee.address, is_warm_access)
        .account_read(callee.address, AccountFieldTag.Balance, callee_balance)
        .account_read(callee.address, AccountFieldTag.Nonce, RLC(callee.nonce, randomness))
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
        .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
    )
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee.code.table_assignments(randomness),
            )
        ),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.ErrorOutOfGasCALL,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=caller_bytecode_hash,
                program_counter=231,
                stack_pointer=1017,
                gas_left=caller_ctx.gas_left,
                memory_size=caller_ctx.memory_size,
                reversible_write_counter=caller_ctx.reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.EndTx,
                rw_counter=rw_dictionary.rw_counter,
                call_id=1,
                gas_left=0,
            ),
        ],
    )


CallerContext = namedtuple(
    "CallerContext",
    [
        "is_root",
        "is_create",
        "program_counter",
        "stack_pointer",
        "gas_left",
        "memory_size",
        "reversible_write_counter",
    ],
    defaults=[False, False, 232, 1023, 10, 0, 0],
)

TESTING_DATA_NOT_ROOT = ((CallerContext(), CALLEE_WITH_STOP_BYTECODE_AND_BALANCE),)


@pytest.mark.parametrize("caller_ctx, callee", TESTING_DATA_NOT_ROOT)
def test_oog_call_not_root(caller_ctx: CallerContext, callee: Account):
    randomness = rand_fq()

    caller_bytecode = Bytecode().call(0, 0xFF, 0, 0, 0, 0, 0).stop()
    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)
    callee_bytecode_hash = RLC(callee.code_hash(), randomness)
    callee_reversible_write_counter = 0

    stack = Stack(gas=100, cd_offset=64, cd_length=320, rd_offset=0, rd_length=32)

    is_warm_access = False
    caller_rw_counter_end_of_reversion = 2

    callee_balance = 200
    callee_balance = RLC(callee_balance + stack.value, randomness)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee.code.table_assignments(randomness),
            )
        ),
        rw_table=set(
            # fmt: off
            RWDictionary(24)
            .call_context_read(2, CallContextFieldTag.TxId, 1)
            .call_context_read(2, CallContextFieldTag.IsStatic, False)
            .stack_read(2, 1017, RLC(stack.gas, randomness))
            .stack_read(2, 1018, RLC(callee.address, randomness))
            .stack_read(2, 1019, RLC(stack.value, randomness))
            .stack_read(2, 1020, RLC(stack.cd_offset, randomness))
            .stack_read(2, 1021, RLC(stack.cd_length, randomness))
            .stack_read(2, 1022, RLC(stack.rd_offset, randomness))
            .stack_read(2, 1023, RLC(stack.rd_length, randomness))
            .stack_write(2, 1023, RLC(False, randomness))
            .tx_access_list_account_read(1, callee.address, is_warm_access)            .account_read(callee.address, AccountFieldTag.Balance, callee_balance)
            .account_read(callee.address, AccountFieldTag.Nonce, RLC(callee.nonce, randomness))
            .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
            # restore context operations
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
                execution_state=ExecutionState.ErrorOutOfGasCALL,
                rw_counter=24,
                call_id=2,
                is_root=False,
                is_create=False,
                code_hash=caller_bytecode_hash,
                program_counter=231,
                stack_pointer=1017,
                gas_left=0,
                reversible_write_counter=callee_reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=24 + 27,
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
