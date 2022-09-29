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
Expected = namedtuple(
    "Expected",
    ["caller_gas_left", "callee_gas_left", "next_memory_size"],
)

STOP_BYTECODE = Bytecode().stop()

CALLER = Account(address=0xFE, balance=int(1e20))
CALLEE_WITH_STOP_BYTECODE_AND_BALANCE = Account(address=0xFF, code=STOP_BYTECODE, balance=int(1e18))


def expected(callee: Account, caller_ctx: CallContext, stack: Stack, is_warm_access: bool):
    def memory_size(offset: int, length: int) -> int:
        if length == 0:
            return 0
        return (offset + length + 31) // 32

    is_account_empty = callee.is_empty()
    has_value = stack.value != 0
    next_memory_size = max(
        memory_size(stack.cd_offset, stack.cd_length),
        memory_size(stack.rd_offset, stack.rd_length),
        caller_ctx.memory_size,
    )
    memory_expansion_gas_cost = (
        next_memory_size * next_memory_size - caller_ctx.memory_size * caller_ctx.memory_size
    ) // 512 + 3 * (next_memory_size - caller_ctx.memory_size)
    gas_cost = (
        (GAS_COST_WARM_ACCESS if is_warm_access else GAS_COST_ACCOUNT_COLD_ACCESS)
        + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_NEW_ACCOUNT)
        + memory_expansion_gas_cost
    )
    gas_available = caller_ctx.gas_left - gas_cost
    all_but_one_64th_gas = gas_available - gas_available // 64
    callee_gas_left = min(all_but_one_64th_gas, stack.gas)
    caller_gas_left = caller_ctx.gas_left - (
        gas_cost - has_value * GAS_STIPEND_CALL_WITH_VALUE
        if callee.code_hash() == EMPTY_CODE_HASH
        else gas_cost + callee_gas_left
    )

    return Expected(
        caller_gas_left=caller_gas_left,
        callee_gas_left=callee_gas_left + has_value * GAS_STIPEND_CALL_WITH_VALUE,
        next_memory_size=next_memory_size,
    )


def gen_testing_data():
    callees = [
        # CALLEE_WITH_NOTHING,
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
            expected(callee, call_context, stack, is_warm_access),
        )
        for callee, call_context, stack, is_warm_access in itertools.product(
            callees, call_contexts, stacks, is_warm_accesss
        )
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "caller, callee, caller_ctx, stack, is_warm_access, expected", TESTING_DATA
)
def test_root_call(
    caller: Account,
    callee: Account,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
    expected: Expected,
):
    randomness = rand_fq()

    caller_balance_prev = RLC(caller.balance, randomness)
    callee_balance_prev = RLC(callee.balance, randomness)
    caller_balance = RLC(caller.balance - stack.value, randomness)
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
    callee_rw_counter_end_of_reversion = 0

    # fmt: off
    rw_dictionary = (
        RWDictionary(24)
        .call_context_read(1, CallContextFieldTag.TxId, 1)
        .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, caller_ctx.rw_counter_end_of_reversion)
        .call_context_read(1, CallContextFieldTag.IsPersistent, caller_ctx.is_persistent)
        .call_context_read(1, CallContextFieldTag.CalleeAddress, caller.address)
        .call_context_read(1, CallContextFieldTag.IsStatic, False)
        .stack_read(1, 1017, RLC(stack.gas, randomness))
        .stack_read(1, 1018, RLC(callee.address, randomness))
        .stack_read(1, 1019, RLC(stack.value, randomness))
        .stack_read(1, 1020, RLC(stack.cd_offset, randomness))
        .stack_read(1, 1021, RLC(stack.cd_length, randomness))
        .stack_read(1, 1022, RLC(stack.rd_offset, randomness))
        .stack_read(1, 1023, RLC(stack.rd_length, randomness))
        .stack_write(1, 1023, RLC(is_success, randomness))
        .tx_access_list_account_write(1, callee.address, True, is_warm_access, rw_counter_of_reversion=caller_ctx.rw_counter_end_of_reversion - caller_ctx.reversible_write_counter)
        .call_context_read(24, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion)
        .call_context_read(24, CallContextFieldTag.IsPersistent, False)
        .account_write(caller.address, AccountFieldTag.Balance, caller_balance, caller_balance_prev, rw_counter_of_reversion=callee_rw_counter_end_of_reversion)
        .account_write(callee.address, AccountFieldTag.Balance, callee_balance, callee_balance_prev, rw_counter_of_reversion=callee_rw_counter_end_of_reversion - 1)
        .account_read(callee.address, AccountFieldTag.Nonce, RLC(callee.nonce, randomness))
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
        .call_context_read(1, CallContextFieldTag.IsSuccess, 0)
        .call_context_read(1, CallContextFieldTag.IsPersistent, 0)
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
    callee_rw_counter_end_of_reversion = 0
    caller_address = 0xFF

    caller_balance = 1000
    callee_balance = 200
    caller_balance_prev = RLC(1000, randomness)
    callee_balance_prev = RLC(200, randomness)
    caller_balance = RLC(caller_balance - stack.value, randomness)
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
            .call_context_read(2, CallContextFieldTag.RwCounterEndOfReversion, caller_rw_counter_end_of_reversion)
            .call_context_read(2, CallContextFieldTag.IsPersistent, False)
            .call_context_read(2, CallContextFieldTag.CalleeAddress, caller_address)
            .call_context_read(2, CallContextFieldTag.IsStatic, False)
            .stack_read(2, 1017, RLC(stack.gas, randomness))
            .stack_read(2, 1018, RLC(callee.address, randomness))
            .stack_read(2, 1019, RLC(stack.value, randomness))
            .stack_read(2, 1020, RLC(stack.cd_offset, randomness))
            .stack_read(2, 1021, RLC(stack.cd_length, randomness))
            .stack_read(2, 1022, RLC(stack.rd_offset, randomness))
            .stack_read(2, 1023, RLC(stack.rd_length, randomness))
            .stack_write(2, 1023, RLC(False, randomness))
            .tx_access_list_account_write(1, callee.address, True, is_warm_access,
                                          rw_counter_of_reversion=caller_rw_counter_end_of_reversion - caller_ctx.reversible_write_counter)
            .call_context_read(24, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion)
            .call_context_read(24, CallContextFieldTag.IsPersistent, False)
            .account_write(caller_address, AccountFieldTag.Balance, caller_balance, caller_balance_prev,
                           rw_counter_of_reversion=callee_rw_counter_end_of_reversion)
            .account_write(callee.address, AccountFieldTag.Balance, callee_balance, callee_balance_prev,
                           rw_counter_of_reversion=callee_rw_counter_end_of_reversion - 1)
            .account_read(callee.address, AccountFieldTag.Nonce, RLC(callee.nonce, randomness))
            .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
            # restore context operations
            .call_context_read(2, CallContextFieldTag.IsSuccess, 0)
            .call_context_read(2, CallContextFieldTag.IsPersistent, 0)
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
                code_hash=callee_bytecode_hash,
                program_counter=0,
                stack_pointer=1017,
                gas_left=0,
                reversible_write_counter=callee_reversible_write_counter,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=24 + 34,
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