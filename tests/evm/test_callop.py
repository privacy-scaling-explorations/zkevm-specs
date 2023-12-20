import pytest
from collections import namedtuple
from itertools import chain, product
from zkevm_specs.evm_circuit import (
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
from zkevm_specs.evm_circuit.table import CopyDataTypeTag
from zkevm_specs.evm_circuit.typing import CopyCircuit
from zkevm_specs.util import (
    EMPTY_CODE_HASH,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_WARM_ACCESS,
    GAS_STIPEND_CALL_WITH_VALUE,
    Word,
    U256,
)
from common import CallContext, rand_fq


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
    is_precheck_ok: bool,
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
        caller_ctx.memory_word_size,
    )
    memory_expansion_gas_cost = (
        next_memory_size * next_memory_size
        - caller_ctx.memory_word_size * caller_ctx.memory_word_size
    ) // 512 + 3 * (next_memory_size - caller_ctx.memory_word_size)
    gas_cost = (
        (GAS_COST_WARM_ACCESS if is_warm_access else GAS_COST_ACCOUNT_COLD_ACCESS)
        + has_value
        * (
            GAS_COST_CALL_WITH_VALUE
            # Only CALL opcode could invoke transfer to make empty account into non-empty.
            + is_precheck_ok * is_call * callee.is_empty() * GAS_COST_NEW_ACCOUNT
        )
        + memory_expansion_gas_cost
    )
    gas_available = caller_ctx.gas_left - gas_cost
    all_but_one_64th_gas = gas_available - gas_available // 64
    callee_gas_left = min(all_but_one_64th_gas, stack.gas)
    caller_gas_left = caller_ctx.gas_left - (
        gas_cost - has_value * GAS_STIPEND_CALL_WITH_VALUE
        if bytecode_hash == EMPTY_CODE_HASH or is_precheck_ok is False
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
        CallContext(
            gas_left=100000, is_persistent=True, memory_word_size=8, reversible_write_counter=5
        ),
        CallContext(
            gas_left=100000,
            is_persistent=False,
            rw_counter_end_of_reversion=88,
            reversible_write_counter=2,
        ),
    ]
    stacks = [
        Stack(),
        Stack(value=int(1e18), gas=100000),
        Stack(value=int(1e18), gas=100, cd_offset=64, cd_length=320, rd_offset=0, rd_length=32),
        Stack(cd_offset=0xFFFFFF, cd_length=0, rd_offset=0xFFFFFF, rd_length=0),
    ]
    is_warm_access = [True, False]
    depths = [1, 1024, 1025]
    return [
        (
            opcode,
            callee,
            call_context,
            stack,
            is_warm_access,
            depth,
            expected(
                opcode,
                callee.code_hash(),
                # `callee = caller` for both CALLCODE and DELEGATECALL opcodes.
                CALLER if opcode in [opcode.CALLCODE, Opcode.DELEGATECALL] else callee,
                call_context,
                stack,
                is_warm_access,
                CALLER.balance >= stack.value and depth < 1025,
            ),
        )
        for opcode, callee, call_context, stack, is_warm_access, depth in product(
            opcodes, callees, call_contexts, stacks, is_warm_access, depths
        )
    ]


TESTING_DATA = gen_testing_data()


def callop_test_template(
    opcode: Opcode,
    callee: Account,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
    depth: int,
    is_precompile: bool,
    expected: Expected,
):
    is_call = 1 if opcode == Opcode.CALL else 0
    is_callcode = 1 if opcode == Opcode.CALLCODE else 0
    is_delegatecall = 1 if opcode == Opcode.DELEGATECALL else 0

    caller = CALLER
    parent_caller = PARENT_CALLER
    parent_value = PARENT_VALUE

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

    callee_bytecode = callee.code
    callee_bytecode_hash = callee_bytecode.hash()
    if not callee.is_empty() and not is_precompile:
        is_empty_code_hash = callee_bytecode_hash == EMPTY_CODE_HASH
    else:
        is_empty_code_hash = True
    callee_bytecode_hash = Word(callee_bytecode_hash if not is_empty_code_hash else 0)

    # Only check balance and stack depth
    is_precheck_ok = caller.balance >= value and depth < 1025
    is_success = is_precheck_ok and callee != CALLEE_WITH_REVERT_BYTECODE
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
        .call_context_read(1, CallContextFieldTag.CalleeAddress, Word(caller.address))
        .call_context_read(1, CallContextFieldTag.IsStatic, is_static)
        .call_context_read(1, CallContextFieldTag.Depth, depth)
    )
    if is_delegatecall == 1:
        rw_dictionary \
        .call_context_read(1, CallContextFieldTag.CallerAddress, Word(parent_caller.address)) \
        .call_context_read(1, CallContextFieldTag.Value, Word(parent_value))
    if is_call + is_callcode == 1:
        rw_dictionary \
        .stack_read(1, 1017, Word(stack.gas)) \
        .stack_read(1, 1018, Word(callee.address)) \
        .stack_read(1, 1019, Word(value))
    else: # DELEGATECALL or STATICCALL
        rw_dictionary \
        .stack_read(1, 1018, Word(stack.gas)) \
        .stack_read(1, 1019, Word(callee.address))

    rw_dictionary \
        .stack_read(1, 1020, Word(stack.cd_offset)) \
        .stack_read(1, 1021, Word(stack.cd_length)) \
        .stack_read(1, 1022, Word(stack.rd_offset)) \
        .stack_read(1, 1023, Word(stack.rd_length)) \
        .stack_write(1, 1023, Word(is_success)) \
        .account_read(callee.address, AccountFieldTag.CodeHash, callee_bytecode_hash) \
        .tx_access_list_account_write(1, callee.address, True, is_warm_access, rw_counter_of_reversion=None if caller_ctx.is_persistent else caller_ctx.rw_counter_end_of_reversion - caller_ctx.reversible_write_counter) \
        .call_context_read(call_id, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion) \
        .call_context_read(call_id, CallContextFieldTag.IsPersistent, callee_is_persistent)
    # fmt: on

    # Read balance only when CALL or CALLCODE
    if is_call + is_callcode == 1:
        rw_dictionary.account_read(caller.address, AccountFieldTag.Balance, caller.balance)

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

    # fmt: off
    if is_call == 1 and is_precheck_ok:
        caller_balance_prev = Word(caller.balance)
        callee_balance_prev = Word(callee.balance)
        caller_balance = Word(caller.balance - value)
        callee_balance = Word(callee.balance + value)
        # For `transfer` invocation.
        rw_dictionary \
            .account_write(caller.address, AccountFieldTag.Balance, caller_balance, caller_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion) \
            .account_write(callee.address, AccountFieldTag.Balance, callee_balance, callee_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion - 1)


    if (is_precheck_ok is False or is_empty_code_hash) and is_precompile is False:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(1, CallContextFieldTag.LastCalleeReturnDataLength, 0)
    elif is_precompile:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.IsSuccess, True) \
        .call_context_write(1, CallContextFieldTag.CalleeAddress, Word(callee.address)) \
        .call_context_write(1, CallContextFieldTag.CallerId, 1) \
        .call_context_write(1, CallContextFieldTag.CallDataOffset, stack.cd_offset) \
        .call_context_write(1, CallContextFieldTag.CallDataLength, stack.cd_length) \
        .call_context_write(1, CallContextFieldTag.ReturnDataOffset, stack.rd_offset) \
        .call_context_write(1, CallContextFieldTag.ReturnDataLength, stack.rd_length) \
        .call_context_write(call_id, CallContextFieldTag.ProgramCounter, next_program_counter) \
        .call_context_write(call_id, CallContextFieldTag.StackPointer, 1023) \
        .call_context_write(call_id, CallContextFieldTag.GasLeft, expected.caller_gas_left) \
        .call_context_write(call_id, CallContextFieldTag.MemorySize, expected.next_memory_size) \
        .call_context_write(call_id, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter + 1) \
        .call_context_write(call_id, CallContextFieldTag.LastCalleeId, call_id) \
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_write(call_id, CallContextFieldTag.LastCalleeReturnDataLength, stack.rd_length)
    else:
        rw_dictionary \
        .call_context_write(1, CallContextFieldTag.ProgramCounter, next_program_counter) \
        .call_context_write(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_write(1, CallContextFieldTag.GasLeft, expected.caller_gas_left) \
        .call_context_write(1, CallContextFieldTag.MemorySize, expected.next_memory_size) \
        .call_context_write(1, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter + 1) \
        .call_context_read(call_id, CallContextFieldTag.CallerId, 1) \
        .call_context_read(call_id, CallContextFieldTag.TxId, 1) \
        .call_context_read(call_id, CallContextFieldTag.Depth, depth + 1) \
        .call_context_read(call_id, CallContextFieldTag.CallerAddress, Word(caller.address)) \
        .call_context_read(call_id, CallContextFieldTag.CalleeAddress, Word(callee.address)) \
        .call_context_read(call_id, CallContextFieldTag.CallDataOffset, stack.cd_offset if stack.cd_length != 0 else 0) \
        .call_context_read(call_id, CallContextFieldTag.CallDataLength, stack.cd_length) \
        .call_context_read(call_id, CallContextFieldTag.ReturnDataOffset, stack.rd_offset if stack.rd_length != 0 else 0) \
        .call_context_read(call_id, CallContextFieldTag.ReturnDataLength, stack.rd_length) \
        .call_context_read(call_id, CallContextFieldTag.Value, Word(parent_value if is_delegatecall == 1 else value)) \
        .call_context_read(call_id, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(call_id, CallContextFieldTag.IsStatic, is_static) \
        .call_context_read(call_id, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_read(call_id, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_read(call_id, CallContextFieldTag.LastCalleeReturnDataLength, 0) \
        .call_context_read(call_id, CallContextFieldTag.IsRoot, False) \
        .call_context_read(call_id, CallContextFieldTag.IsCreate, False) \
        .call_context_read(call_id, CallContextFieldTag.CodeHash, callee_bytecode_hash)
    # fmt: on

    return (
        caller_bytecode,
        callee_bytecode,
        call_id,
        next_program_counter,
        stack_pointer,
        rw_dictionary,
        is_precheck_ok,
        is_empty_code_hash,
    )


@pytest.mark.parametrize(
    "opcode, callee, caller_ctx, stack, is_warm_access, depth, expected",
    TESTING_DATA,
)
def test_callop(
    opcode: Opcode,
    callee: Account,
    caller_ctx: CallContext,
    stack: Stack,
    is_warm_access: bool,
    depth: int,
    expected: Expected,
):
    (
        caller_bytecode,
        callee_bytecode,
        call_id,
        next_program_counter,
        stack_pointer,
        rw_dictionary,
        is_precheck_ok,
        is_empty_code_hash,
    ) = callop_test_template(
        opcode, callee, caller_ctx, stack, is_warm_access, depth, False, expected
    )

    caller_bytecode_hash = Word(caller_bytecode.hash())
    callee_bytecode_hash = Word(callee_bytecode.hash() if not callee.is_empty() else 0)
    rw_counter = call_id

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(),
                callee_bytecode.table_assignments(),
            )
        ),
        rw_table=set(rw_dictionary.rws),
    )

    verify_steps(
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
                memory_word_size=caller_ctx.memory_word_size,
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
                if is_empty_code_hash or is_precheck_ok is False
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


def gen_precompile_testing_data():
    opcodes = [
        Opcode.CALL,
        # Opcode.CALLCODE,
        # Opcode.DELEGATECALL,
        # Opcode.STATICCALL,
    ]
    precompiles = [
        (
            ExecutionState.ECRECOVER,
            Account(
                address=1,
                code=Bytecode()
                .push32(0x456E9AEA5E197A1F1AF7A3E85A3212FA4049A3BA34C2289B4C860FC0B0C64EF3)
                .push1(0)
                .mstore()
                .push1(28)  # v
                .push1(0x20)
                .mstore()
                .push32(0x9242685BF161793CC25603C231BC2F568EB630EA16AA137D2664AC8038825608)  # r
                .push1(0x40)
                .mstore()
                .push32(0x4F8AE3BD7535248D0BD448298CC2E2071E56992D0774DC340C368AE950852ADA)  # s
                .push1(0x60)
                .mstore(),
            ),
            Stack(cd_offset=0, cd_length=0x80, rd_offset=0, rd_length=0x20),
        )
    ]

    return [(opcode, callee) for opcode, callee in product(opcodes, precompiles)]


PRECOMPILE_TESTING_DATA = gen_precompile_testing_data()

PRECOMPILE_RETURN_DATA = [0x01] * 64


@pytest.mark.parametrize(
    "opcode, precompile",
    PRECOMPILE_TESTING_DATA,
)
def test_callop_precompiles(opcode: Opcode, precompile: tuple[Account, Stack]):
    randomness_keccak = rand_fq()

    exe_state = precompile[0]
    callee = precompile[1]
    stack = precompile[2]
    caller_ctx = CallContext(gas_left=100000)
    expectation = expected(
        opcode,
        callee.code_hash(),
        CALLER if opcode in [opcode.CALLCODE, Opcode.DELEGATECALL] else callee,
        caller_ctx,
        stack,
        True,
        True,
    )

    (
        caller_bytecode,
        callee_bytecode,
        call_id,
        next_program_counter,
        stack_pointer,
        rw_dictionary,
        _,
        _,
    ) = callop_test_template(
        opcode,
        callee,
        caller_ctx,
        stack,
        True,
        1,
        True,
        expectation,
    )

    caller_bytecode_hash = Word(caller_bytecode.hash())
    rw_counter = call_id

    src_data = dict(
        [
            (i, PRECOMPILE_RETURN_DATA[i] if i < len(PRECOMPILE_RETURN_DATA) else 0)
            for i in range(0, stack.rd_length)
        ]
    )
    copy_circuit = CopyCircuit().copy(
        randomness_keccak,
        rw_dictionary,
        call_id,
        CopyDataTypeTag.Memory,
        1,
        CopyDataTypeTag.Memory,
        0,
        stack.rd_length,
        0,
        stack.rd_length,
        src_data,
    )

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        withdrawal_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(),
                callee_bytecode.table_assignments(),
            )
        ),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    verify_steps(
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
                memory_word_size=caller_ctx.memory_word_size,
                reversible_write_counter=caller_ctx.reversible_write_counter,
                aux_data=[stack.rd_length],
            ),
            StepState(
                execution_state=exe_state,
                rw_counter=rw_dictionary.rw_counter,
                call_id=call_id,
                is_root=False,
                is_create=False,
                code_hash=Word(EMPTY_CODE_HASH),
                program_counter=next_program_counter,
                stack_pointer=stack_pointer,
                gas_left=expectation.callee_gas_left,
                reversible_write_counter=2,
                memory_word_size=int((stack.rd_length + 31) / 32),
            ),
        ],
    )
