import pytest
from collections import namedtuple
from itertools import chain, product
from zkevm_specs.evm import (
    Account,
    AccountFieldTag,
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
from zkevm_specs.util import (
    EMPTY_CODE_HASH,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_WARM_ACCESS,
    GAS_STIPEND_CALL_WITH_VALUE,
    RLC,
    U256,
    rand_fq,
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

PARENT_CALLER = Account(address=0xFD, balance=int(1e20))
PARENT_VALUE = int(5e18)

CALLER = Account(address=0xFE, balance=int(1e20))
CALLEE_WITH_NOTHING = Account(address=0xFF)
CALLEE_WITH_STOP_BYTECODE_AND_BALANCE = Account(address=0xFF, code=STOP_BYTECODE, balance=int(1e18))
CALLEE_WITH_RETURN_BYTECODE = Account(address=0xFF, code=RETURN_BYTECODE)
CALLEE_WITH_REVERT_BYTECODE = Account(address=0xFF, code=REVERT_BYTECODE)


def expected(
    opcode: Opcode,
    bytecode_hash: U256,
    callee: Account,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
):
    def memory_size(offset: int, length: int) -> int:
        if length == 0:
            return 0
        return (offset + length + 31) // 32

    is_call = 1 if opcode == Opcode.CALL else 0
    # Both CALL and CALLCODE opcodes have argument `value` on stack, but no for
    # DELEGATECALL or STATICCALL.
    has_value = stack.value != 0 if opcode in [Opcode.CALL, Opcode.CALLCODE] else False
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
        + has_value
        * (
            GAS_COST_CALL_WITH_VALUE
            # Only CALL opcode could invoke transfer to make empty account into non-empty.
            + is_call * callee.is_empty() * GAS_COST_NEW_ACCOUNT
        )
        + memory_expansion_gas_cost
    )
    gas_available = caller_ctx.gas_left - gas_cost
    all_but_one_64th_gas = gas_available - gas_available // 64
    callee_gas_left = min(all_but_one_64th_gas, stack.gas)
    caller_gas_left = caller_ctx.gas_left - (
        gas_cost - has_value * GAS_STIPEND_CALL_WITH_VALUE
        if bytecode_hash == EMPTY_CODE_HASH
        else gas_cost + callee_gas_left
    )

    return Expected(
        caller_gas_left=caller_gas_left,
        callee_gas_left=callee_gas_left + has_value * GAS_STIPEND_CALL_WITH_VALUE,
        next_memory_size=next_memory_size,
    )


def gen_testing_data():
    opcodes = [
        Opcode.CALL,
        Opcode.CALLCODE,
        Opcode.DELEGATECALL,
        Opcode.STATICCALL,
    ]
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
            opcode,
            CALLER,
            callee,
            PARENT_CALLER,
            PARENT_VALUE,
            call_context,
            stack,
            is_warm_access,
            expected(
                opcode,
                callee.code_hash(),
                # `callee = caller` for both CALLCODE and DELEGATECALL opcodes.
                CALLER if opcode in [opcode.CALLCODE, Opcode.DELEGATECALL] else callee,
                call_context,
                stack,
                is_warm_access,
            ),
        )
        for opcode, callee, call_context, stack, is_warm_access in product(
            opcodes, callees, call_contexts, stacks, is_warm_accesss
        )
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "opcode, caller, callee, parent_caller, parent_value, caller_ctx, stack, is_warm_access, expected",
    TESTING_DATA,
)
def test_callop(
    opcode: Opcode,
    caller: Account,
    callee: Account,
    parent_caller: Account,
    parent_value: int,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
    expected: Expected,
):
    randomness = rand_fq()

    is_call = 1 if opcode == Opcode.CALL else 0
    is_callcode = 1 if opcode == Opcode.CALLCODE else 0
    is_delegatecall = 1 if opcode == Opcode.DELEGATECALL else 0
    is_staticcall = 1 if opcode == Opcode.STATICCALL else 0

    # Set `is_static == 1` for both DELEGATECALL and STATICCALL opcodes, or when
    # `stack.value == 0` for both CALL and CALLCODE opcodes.
    value = stack.value if is_call + is_callcode == 1 else 0
    is_static = value == 0

    if is_call == 1:
        caller_bytecode = (
            Bytecode()
            .call(
                stack.gas,
                callee.address,
                value,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    elif is_callcode == 1:
        caller_bytecode = (
            Bytecode()
            .callcode(
                stack.gas,
                callee.address,
                value,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    elif is_delegatecall == 1:
        caller_bytecode = (
            Bytecode()
            .delegatecall(
                stack.gas,
                callee.address,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )
    else:  # STATICCALL
        caller_bytecode = (
            Bytecode()
            .staticcall(
                stack.gas,
                callee.address,
                stack.cd_offset,
                stack.cd_length,
                stack.rd_offset,
                stack.rd_length,
            )
            .stop()
        )

    caller_bytecode_hash = RLC(caller_bytecode.hash(), randomness)

    callee_bytecode = callee.code
    callee_bytecode_hash = callee_bytecode.hash()
    if not callee.is_empty():
        is_empty_code_hash = callee_bytecode_hash == EMPTY_CODE_HASH
    else:
        is_empty_code_hash = True
    callee_bytecode_hash = RLC(callee_bytecode_hash if not callee.is_empty() else 0, randomness)

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

    # For CALL opcode, it has an extra stack pop `value` and two account write for `transfer` call (+3).
    # For CALLCODE opcode, it has an extra stack pop `value` and one account read for caller balance (+2).
    # For DELEGATECALL opcode, it has two extra call context lookups for current caller address and value (+2).
    # No extra lookups for STATICCALL opcode.
    call_id = 20 + is_call * 3 + is_callcode * 2 + is_delegatecall * 2
    rw_counter = call_id
    next_program_counter = 232 if is_call + is_callcode == 1 else 199
    stack_pointer = 1018 - is_call - is_callcode

    # fmt: off
    rw_dictionary = (
        RWDictionary(rw_counter)
        .call_context_read(1, CallContextFieldTag.TxId, 1)
        .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, caller_ctx.rw_counter_end_of_reversion)
        .call_context_read(1, CallContextFieldTag.IsPersistent, caller_ctx.is_persistent)
        .call_context_read(1, CallContextFieldTag.CalleeAddress, caller.address)
        .call_context_read(1, CallContextFieldTag.IsStatic, is_static)
        .call_context_read(1, CallContextFieldTag.Depth, 1)
    )
    if is_delegatecall == 1:
        rw_dictionary \
        .call_context_read(1, CallContextFieldTag.CallerAddress, parent_caller.address) \
        .call_context_read(1, CallContextFieldTag.Value, RLC(parent_value, randomness))
    if is_call + is_callcode == 1:
        rw_dictionary \
        .stack_read(1, 1017, RLC(stack.gas, randomness)) \
        .stack_read(1, 1018, RLC(callee.address, randomness)) \
        .stack_read(1, 1019, RLC(value, randomness))
    else: # DELEGATECALL or STATICCALL
        rw_dictionary \
        .stack_read(1, 1018, RLC(stack.gas, randomness)) \
        .stack_read(1, 1019, RLC(callee.address, randomness))

    rw_dictionary \
        .stack_read(1, 1020, RLC(stack.cd_offset, randomness)) \
        .stack_read(1, 1021, RLC(stack.cd_length, randomness)) \
        .stack_read(1, 1022, RLC(stack.rd_offset, randomness)) \
        .stack_read(1, 1023, RLC(stack.rd_length, randomness)) \
        .stack_write(1, 1023, RLC(is_success, randomness)) \
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash) \
        .tx_access_list_account_write(1, callee.address, True, is_warm_access, rw_counter_of_reversion=None if caller_ctx.is_persistent else caller_ctx.rw_counter_end_of_reversion - caller_ctx.reversible_write_counter) \
        .call_context_read(call_id, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion) \
        .call_context_read(call_id, CallContextFieldTag.IsPersistent, callee_is_persistent)
    # fmt: on

    # For opcode CALLCODE:
    # - callee = caller
    #
    # For opcode DELEGATECALL:
    # - callee = caller
    # - caller = parent_caller
    if is_callcode == 1:
        callee = caller
    elif is_delegatecall == 1:
        callee = caller
        caller = parent_caller

    caller_balance_prev = RLC(caller.balance, randomness)
    callee_balance_prev = RLC(callee.balance, randomness)
    caller_balance = RLC(caller.balance - value, randomness)
    callee_balance = RLC(callee.balance + value, randomness)

    # fmt: off
    if is_call == 1:
        # For `transfer` invocation.
        rw_dictionary \
            .account_write(caller.address, AccountFieldTag.Balance, caller_balance, caller_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion) \
            .account_write(callee.address, AccountFieldTag.Balance, callee_balance, callee_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion - 1)
    elif is_callcode == 1:
        # Get caller balance to constrain it should be greater than or equal to stack `value`.
        rw_dictionary \
            .account_read(caller.address, AccountFieldTag.Balance, RLC(caller.balance, randomness))

    if is_empty_code_hash:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    else:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.ProgramCounter, next_program_counter) \
        .call_context_write(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_write(1, CallContextFieldTag.GasLeft, expected.caller_gas_left) \
        .call_context_write(1, CallContextFieldTag.MemorySize, expected.next_memory_size) \
        .call_context_write(1, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter + 1) \
        .call_context_read(call_id, CallContextFieldTag.CallerId, 1) \
        .call_context_read(call_id, CallContextFieldTag.TxId, 1) \
        .call_context_read(call_id, CallContextFieldTag.Depth, 2) \
        .call_context_read(call_id, CallContextFieldTag.CallerAddress, caller.address) \
        .call_context_read(call_id, CallContextFieldTag.CalleeAddress, callee.address) \
        .call_context_read(call_id, CallContextFieldTag.CallDataOffset, stack.cd_offset if stack.cd_length != 0 else 0) \
        .call_context_read(call_id, CallContextFieldTag.CallDataLength, stack.cd_length) \
        .call_context_read(call_id, CallContextFieldTag.ReturnDataOffset, stack.rd_offset if stack.rd_length != 0 else 0) \
        .call_context_read(call_id, CallContextFieldTag.ReturnDataLength, stack.rd_length) \
        .call_context_read(call_id, CallContextFieldTag.Value, RLC(parent_value if is_delegatecall == 1 else value, randomness)) \
        .call_context_read(call_id, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(call_id, CallContextFieldTag.IsStatic, is_static) \
        .call_context_read(call_id, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_read(call_id, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_read(call_id, CallContextFieldTag.LastCalleeReturnDataLength, 0) \
        .call_context_read(call_id, CallContextFieldTag.IsRoot, False) \
        .call_context_read(call_id, CallContextFieldTag.IsCreate, False) \
        .call_context_read(call_id, CallContextFieldTag.CodeHash, callee_bytecode_hash)
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee_bytecode.table_assignments(randomness),
            )
        ),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CALL_OP,
                rw_counter=rw_counter,
                call_id=1,
                is_root=True,
                is_create=False,
                code_hash=caller_bytecode_hash,
                program_counter=next_program_counter - 1,
                stack_pointer=stack_pointer,
                gas_left=caller_ctx.gas_left,
                memory_word_size=caller_ctx.memory_size,
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
                    program_counter=next_program_counter,
                    stack_pointer=1023,
                    gas_left=expected.caller_gas_left,
                    memory_word_size=expected.next_memory_size,
                    reversible_write_counter=caller_ctx.reversible_write_counter + 3,
                )
                if is_empty_code_hash
                else StepState(
                    execution_state=ExecutionState.STOP
                    if callee.code == STOP_BYTECODE
                    else ExecutionState.PUSH,
                    rw_counter=rw_dictionary.rw_counter,
                    call_id=call_id,
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
