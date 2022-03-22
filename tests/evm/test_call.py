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
    EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_EMPTY_ACCOUNT,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_WARM_ACCESS,
)

CallContext = namedtuple(
    "CallContext",
    [
        "rw_counter_end_of_reversion",
        "is_persistent",
        "is_static",
        "gas_left",
        "memory_size",
        "state_write_counter",
    ],
    defaults=[0, True, False, 0, 0, 2],
)
Stack = namedtuple(
    "Stack",
    ["gas", "value", "cd_offset", "cd_length", "rd_offset", "rd_length"],
    defaults=[0, 0, 0, 0, 0, 0],
)
Expected = namedtuple(
    "Expected",
    ["caller_gas_left", "callee_gas_left", "caller_memory_size"],
)

STOP_BYTECODE = Bytecode().stop()
RETURN_BYTECODE = Bytecode().return_(0, 0)
REVERT_BYTECODE = Bytecode().revert(0, 0)

CALLER = Account(address=0xFE, balance=int(1e20))
CALLEE_WITH_NOTHING = Account(address=0xFF)
CALLEE_WITH_STOP_BYTECODE_AND_BALANCE = Account(address=0xFF, code=STOP_BYTECODE, balance=int(1e18))
CALLEE_WITH_RETURN_BYTECODE = Account(address=0xFF, code=RETURN_BYTECODE)
CALLEE_WITH_REVERT_BYTECODE = Account(address=0xFF, code=REVERT_BYTECODE)

TESTING_DATA = (
    # Transfer 1 ether to empty account, successfully
    (
        CALLER,
        CALLEE_WITH_NOTHING,
        CallContext(gas_left=37000, is_persistent=True, is_static=False),
        Stack(value=int(1e18)),
        Expected(caller_gas_left=400, callee_gas_left=2300, caller_memory_size=0),
    ),
    # Transfer 1 ether to non-empty account, successfully
    (
        CALLER,
        CALLEE_WITH_STOP_BYTECODE_AND_BALANCE,
        CallContext(gas_left=12000, is_persistent=True, is_static=False),
        Stack(value=int(1e18)),
        Expected(caller_gas_left=400, callee_gas_left=2300, caller_memory_size=0),
    ),
    # Transfer 1 ether to contract, caller reverts, callee succeeds
    (
        CALLER,
        CALLEE_WITH_RETURN_BYTECODE,
        CallContext(
            gas_left=12000, rw_counter_end_of_reversion=88, is_persistent=False, is_static=False
        ),
        Stack(value=int(1e18)),
        Expected(caller_gas_left=400, callee_gas_left=2300, caller_memory_size=0),
    ),
    # Transfer 1 ether to contract, caller succeeds, callee reverts
    (
        CALLER,
        CALLEE_WITH_REVERT_BYTECODE,
        CallContext(gas_left=12000, is_persistent=True, is_static=False),
        Stack(value=int(1e18)),
        Expected(caller_gas_left=400, callee_gas_left=2300, caller_memory_size=0),
    ),
    # Transfer 1 ether to contract, caller reverts, callee reverts
    (
        CALLER,
        CALLEE_WITH_REVERT_BYTECODE,
        CallContext(
            gas_left=12000, rw_counter_end_of_reversion=88, is_persistent=False, is_static=False
        ),
        Stack(value=int(1e18)),
        Expected(caller_gas_left=400, callee_gas_left=2300, caller_memory_size=0),
    ),
    # Call contract with 0 gas in stack
    (
        CALLER,
        CALLEE_WITH_RETURN_BYTECODE,
        CallContext(gas_left=3000, is_persistent=True, is_static=False),
        Stack(),
        Expected(caller_gas_left=400, callee_gas_left=0, caller_memory_size=0),
    ),
    # Call contract with gas less than cap in stack
    (
        CALLER,
        CALLEE_WITH_RETURN_BYTECODE,
        CallContext(gas_left=3000, is_persistent=True, is_static=False),
        Stack(gas=100),
        Expected(caller_gas_left=300, callee_gas_left=100, caller_memory_size=0),
    ),
    # Call contract with gas greater than cap in stack
    (
        CALLER,
        CALLEE_WITH_RETURN_BYTECODE,
        CallContext(gas_left=3000, is_persistent=True, is_static=False),
        Stack(gas=400),
        Expected(caller_gas_left=6, callee_gas_left=394, caller_memory_size=0),
    ),
    # Call contract with memory expansion by call data
    (
        CALLER,
        CALLEE_WITH_RETURN_BYTECODE,
        CallContext(gas_left=3000, is_persistent=True, is_static=False),
        Stack(cd_offset=64, cd_length=32, rd_offset=0, rd_length=32),
        Expected(caller_gas_left=391, callee_gas_left=0, caller_memory_size=3),
    ),
    # Call contract with memory expansion by return data
    (
        CALLER,
        CALLEE_WITH_RETURN_BYTECODE,
        CallContext(gas_left=3000, is_persistent=True, is_static=False),
        Stack(cd_offset=0, cd_length=32, rd_offset=64, rd_length=32),
        Expected(caller_gas_left=391, callee_gas_left=0, caller_memory_size=3),
    ),
)


@pytest.mark.parametrize("caller, callee, caller_ctx, stack, expected", TESTING_DATA)
def test_call(
    caller: Account, callee: Account, caller_ctx: CallContext, stack: Stack, expected: Expected
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

    is_success = False if callee is CALLEE_WITH_REVERT_BYTECODE else True
    is_reverted_by_caller = not caller_ctx.is_persistent and is_success
    is_reverted_by_callee = not is_success
    callee_is_persistent = caller_ctx.is_persistent and is_success
    callee_rw_counter_end_of_reversion = (
        80
        if is_reverted_by_callee
        else (
            caller_ctx.rw_counter_end_of_reversion - (caller_ctx.state_write_counter + 1)
            if is_reverted_by_caller
            else 0
        )
    )
    is_warm_access = False
    is_account_empty = callee.is_empty()
    has_value = stack.value != 0
    memory_expansion_gas_cost = (
        expected.caller_memory_size * expected.caller_memory_size
        - caller_ctx.memory_size * caller_ctx.memory_size
    ) // 512 + 3 * (expected.caller_memory_size - caller_ctx.memory_size)
    gas_cost = (
        GAS_COST_WARM_ACCESS
        + (1 - is_warm_access) * EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS
        + is_account_empty * GAS_COST_CALL_EMPTY_ACCOUNT
        + has_value * GAS_COST_CALL_WITH_VALUE
        + memory_expansion_gas_cost
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
        .tx_access_list_account_write(1, callee.address, 1, 0, rw_counter_of_reversion=None if caller_ctx.is_persistent else caller_ctx.rw_counter_end_of_reversion - caller_ctx.state_write_counter)
        .call_context_read(24, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion)
        .call_context_read(24, CallContextFieldTag.IsPersistent, callee_is_persistent)
        .account_write(caller.address, AccountFieldTag.Balance, caller_balance, caller_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion)
        .account_write(callee.address, AccountFieldTag.Balance, callee_balance, callee_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion - 1)
        .account_read(callee.address, AccountFieldTag.Nonce, RLC(0, randomness))
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
        .call_context_write(1, CallContextFieldTag.MemorySize, expected.caller_memory_size) \
        .call_context_write(1, CallContextFieldTag.StateWriteCounter, caller_ctx.state_write_counter + 1) \
        .call_context_read(24, CallContextFieldTag.CallerId, 1) \
        .call_context_read(24, CallContextFieldTag.TxId, 1) \
        .call_context_read(24, CallContextFieldTag.Depth, 2) \
        .call_context_read(24, CallContextFieldTag.CallerAddress, caller.address) \
        .call_context_read(24, CallContextFieldTag.CalleeAddress, callee.address) \
        .call_context_read(24, CallContextFieldTag.CallDataOffset, stack.cd_offset) \
        .call_context_read(24, CallContextFieldTag.CallDataLength, stack.cd_length) \
        .call_context_read(24, CallContextFieldTag.ReturnDataOffset, stack.rd_offset) \
        .call_context_read(24, CallContextFieldTag.ReturnDataLength, stack.rd_length) \
        .call_context_read(24, CallContextFieldTag.Value, RLC(stack.value, randomness)) \
        .call_context_read(24, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(24, CallContextFieldTag.IsStatic, caller_ctx.is_static) \
        .call_context_read(24, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_read(24, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_read(24, CallContextFieldTag.LastCalleeReturnDataLength, 0) \
        .call_context_read(24, CallContextFieldTag.IsRoot, False) \
        .call_context_read(24, CallContextFieldTag.IsCreate, False) \
        .call_context_read(24, CallContextFieldTag.CodeSource, callee_bytecode_hash)
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
                execution_state=ExecutionState.CALL,
                rw_counter=24,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=caller_bytecode_hash,
                program_counter=231,
                stack_pointer=1017,
                gas_left=caller_ctx.gas_left,
                memory_size=caller_ctx.memory_size,
                state_write_counter=caller_ctx.state_write_counter,
            ),
            (
                StepState(
                    execution_state=ExecutionState.STOP,
                    rw_counter=rw_dictionary.rw_counter,
                    call_id=1,
                    is_root=True,
                    is_create=False,
                    code_source=caller_bytecode_hash,
                    program_counter=232,
                    stack_pointer=1023,
                    gas_left=caller_ctx.gas_left - gas_cost,
                    state_write_counter=caller_ctx.state_write_counter + 3,
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
                    code_source=callee_bytecode_hash,
                    program_counter=0,
                    stack_pointer=1024,
                    gas_left=expected.callee_gas_left,
                    state_write_counter=2,
                )
            ),
        ],
    )
