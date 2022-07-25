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
    defaults=[0, True, 0, 0, 2],
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
RETURN_BYTECODE = Bytecode().return_(0, 0)
REVERT_BYTECODE = Bytecode().revert(0, 0)

CALLER = Account(address=0xFE, balance=int(1e20))
CALLEE_WITH_NOTHING = Account(address=0xFF)
CALLEE_WITH_STOP_BYTECODE_AND_BALANCE = Account(address=0xFF, code=STOP_BYTECODE, balance=int(1e18))
CALLEE_WITH_RETURN_BYTECODE = Account(address=0xFF, code=RETURN_BYTECODE)
CALLEE_WITH_REVERT_BYTECODE = Account(address=0xFF, code=REVERT_BYTECODE)


def expected(callee: Account, caller_ctx: CallContext, stack: Stack, is_warm_access: bool):
    def memory_size(offset: int, length: int) -> int:
        if length == 0:
            return 0
        return (offset + length + 31) // 32

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
        + has_value * GAS_COST_CALL_WITH_VALUE
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
        CALLEE_WITH_NOTHING,
        CALLEE_WITH_STOP_BYTECODE_AND_BALANCE,
        CALLEE_WITH_RETURN_BYTECODE,
        CALLEE_WITH_REVERT_BYTECODE,
    ]
    call_contexts = [
        CallContext(gas_left=100000, is_persistent=True),
        CallContext(gas_left=100000, is_persistent=True, memory_size=8, reversible_write_counter=5),
        CallContext(gas_left=100000, is_persistent=False, rw_counter_end_of_reversion=88),
    ]
    stacks = [
        Stack(),
        Stack(value=int(1e18)),
        Stack(gas=100),
        Stack(gas=100000),
        Stack(cd_offset=64, cd_length=320, rd_offset=0, rd_length=32),
        Stack(cd_offset=0, cd_length=32, rd_offset=64, rd_length=320),
        Stack(cd_offset=0xFFFFFF, cd_length=0, rd_offset=0xFFFFFF, rd_length=0),
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
def test_callcode(
    caller: Account,
    callee: Account,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
    expected: Expected,
):
    randomness = rand_fq()

    caller_bytecode = (
        Bytecode()
        .callcode(
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

    is_success = False if callee is CALLEE_WITH_REVERT_BYTECODE else True
    is_reverted_by_caller = not caller_ctx.is_persistent and is_success
    is_reverted_by_callee = not is_success
    callee_is_persistent = caller_ctx.is_persistent and is_success
    callee_rw_counter_end_of_reversion = (
        80
        if is_reverted_by_callee
        else (
            caller_ctx.rw_counter_end_of_reversion - (caller_ctx.reversible_write_counter + 1)
            if is_reverted_by_caller
            else 0
        )
    )

    # fmt: off
    rw_dictionary = (
        RWDictionary(24)
        .call_context_read(1, CallContextFieldTag.TxId, 1)
        .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, caller_ctx.rw_counter_end_of_reversion)
        .call_context_read(1, CallContextFieldTag.IsPersistent, caller_ctx.is_persistent)
        .call_context_read(1, CallContextFieldTag.CalleeAddress, caller.address)
        .call_context_read(1, CallContextFieldTag.IsStatic, False)
        .call_context_read(1, CallContextFieldTag.Depth, 1)
        .stack_read(1, 1017, RLC(stack.gas, randomness))
        .stack_read(1, 1018, RLC(callee.address, randomness))
        .stack_read(1, 1019, RLC(stack.value, randomness))
        .stack_read(1, 1020, RLC(stack.cd_offset, randomness))
        .stack_read(1, 1021, RLC(stack.cd_length, randomness))
        .stack_read(1, 1022, RLC(stack.rd_offset, randomness))
        .stack_read(1, 1023, RLC(stack.rd_length, randomness))
        .stack_write(1, 1023, RLC(is_success, randomness))
        .tx_access_list_account_write(1, callee.address, True, is_warm_access, rw_counter_of_reversion=None if caller_ctx.is_persistent else caller_ctx.rw_counter_end_of_reversion - caller_ctx.reversible_write_counter)
        .call_context_read(24, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion)
        .call_context_read(24, CallContextFieldTag.IsPersistent, callee_is_persistent)
        .account_read(caller.address, AccountFieldTag.Balance, RLC(caller.balance, randomness))
        .account_read(callee.address, AccountFieldTag.Nonce, RLC(callee.nonce, randomness))
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash)
    )
    # fmt: on

    # fmt: off
    if callee.code_hash() == EMPTY_CODE_HASH:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    else:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.ProgramCounter, 232) \
        .call_context_write(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_write(1, CallContextFieldTag.GasLeft, expected.caller_gas_left) \
        .call_context_write(1, CallContextFieldTag.MemorySize, expected.next_memory_size) \
        .call_context_write(1, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter + 1) \
        .call_context_read(24, CallContextFieldTag.CallerId, 1) \
        .call_context_read(24, CallContextFieldTag.TxId, 1) \
        .call_context_read(24, CallContextFieldTag.Depth, 2) \
        .call_context_read(24, CallContextFieldTag.CallerAddress, caller.address) \
        .call_context_read(24, CallContextFieldTag.CalleeAddress, callee.address) \
        .call_context_read(24, CallContextFieldTag.CallDataOffset, stack.cd_offset if stack.cd_length != 0 else 0) \
        .call_context_read(24, CallContextFieldTag.CallDataLength, stack.cd_length) \
        .call_context_read(24, CallContextFieldTag.ReturnDataOffset, stack.rd_offset if stack.rd_length != 0 else 0) \
        .call_context_read(24, CallContextFieldTag.ReturnDataLength, stack.rd_length) \
        .call_context_read(24, CallContextFieldTag.Value, RLC(stack.value, randomness)) \
        .call_context_read(24, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(24, CallContextFieldTag.IsStatic, False) \
        .call_context_read(24, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_read(24, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_read(24, CallContextFieldTag.LastCalleeReturnDataLength, 0) \
        .call_context_read(24, CallContextFieldTag.IsRoot, False) \
        .call_context_read(24, CallContextFieldTag.IsCreate, False) \
        .call_context_read(24, CallContextFieldTag.CodeHash, callee_bytecode_hash)
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
                execution_state=ExecutionState.CALLCtx,
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
            (
                StepState(
                    execution_state=ExecutionState.STOP,
                    rw_counter=rw_dictionary.rw_counter,
                    call_id=1,
                    is_root=True,
                    is_create=False,
                    code_hash=caller_bytecode_hash,
                    program_counter=232,
                    stack_pointer=1023,
                    gas_left=expected.caller_gas_left,
                    memory_size=expected.next_memory_size,
                    reversible_write_counter=caller_ctx.reversible_write_counter + 3,
                )
                if callee.code_hash() == EMPTY_CODE_HASH
                else StepState(
                    execution_state=ExecutionState.STOP
                    if callee.code == STOP_BYTECODE
                    else ExecutionState.PUSH,
                    rw_counter=rw_dictionary.rw_counter,
                    call_id=24,
                    is_root=False,
                    is_create=False,
                    code_hash=callee_bytecode_hash,
                    program_counter=0,
                    stack_pointer=1024,
                    gas_left=expected.callee_gas_left,
                    reversible_write_counter=2,
                )
            ),
        ],
    )
