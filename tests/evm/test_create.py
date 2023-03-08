import pytest
import rlp
from collections import namedtuple
from itertools import chain, product
from zkevm_specs.copy_circuit import verify_copy_table
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
from zkevm_specs.evm.table import CopyDataTypeTag
from zkevm_specs.evm.typing import CopyCircuit
from zkevm_specs.util import RLC, rand_fq, keccak256
from zkevm_specs.util.arithmetic import FQ
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import GAS_COST_CREATE

CreateContext = namedtuple(
    "CreateContext",
    [
        "rw_counter_end_of_reversion",
        "is_persistent",
        "gas_left",
        "memory_word_size",
        "reversible_write_counter",
    ],
    defaults=[0, True, 0, 0, 2],
)
Stack = namedtuple(
    "Stack",
    ["value", "offset", "size", "salt"],
    defaults=[0, 0, 0, 0],
)
Expected = namedtuple(
    "Expected",
    ["caller_gas_left", "callee_gas_left", "next_memory_size"],
)

RETURN_BYTECODE = Bytecode().push(0, 1).push(0, 1).return_()
REVERT_BYTECODE = Bytecode().push(0, 1).push(0, 1).revert()

CALLER = Account(address=0xFE, balance=int(1e20), nonce=10)


def expected(
    opcode: Opcode,
    caller_ctx: CreateContext,
    stack: Stack,
):
    def memory_size(offset: int, length: int) -> int:
        if length == 0:
            return 0
        return (offset + length + 31) // 32

    is_create2 = 1 if opcode == Opcode.CREATE2 else 0

    value = stack.value
    offset = stack.offset
    size = stack.size
    if is_create2:
        salt = stack.salt

    next_memory_size = max(
        memory_size(offset, size),
        caller_ctx.memory_word_size,
    )
    memory_expansion_gas_cost = (
        next_memory_size * next_memory_size
        - caller_ctx.memory_word_size * caller_ctx.memory_word_size
    ) // 512 + 3 * (next_memory_size - caller_ctx.memory_word_size)

    # GAS_COST_CODE_DEPOSIT * (bytecode size) is not included here, it should be `return_revert``
    gas_cost = GAS_COST_CREATE + memory_expansion_gas_cost
    gas_available = caller_ctx.gas_left - int(gas_cost)
    all_but_one_64th_gas = gas_available - gas_available // 64
    callee_gas_left = min(all_but_one_64th_gas, caller_ctx.gas_left)
    caller_gas_left = caller_ctx.gas_left - (gas_cost + callee_gas_left)

    return Expected(
        caller_gas_left=caller_gas_left,
        callee_gas_left=callee_gas_left,
        next_memory_size=next_memory_size,
    )


def gen_testing_data():
    opcodes = [
        Opcode.CREATE,
        # Opcode.CREATE2,
    ]
    callee_init_codes = [
        RETURN_BYTECODE,
        REVERT_BYTECODE,
    ]
    create_contexts = [
        CreateContext(gas_left=1_000_000, is_persistent=True),
        CreateContext(gas_left=1_000_000, is_persistent=False, rw_counter_end_of_reversion=88),
    ]
    stacks = [
        Stack(value=int(1e18), offset=64, size=32),
        Stack(offset=64, size=32),
        Stack(offset=0, size=32),
    ]
    is_warm_accesss = [True, False]

    return [
        (
            opcode,
            CALLER,
            callee_init_codes,
            create_contexts,
            stack,
            is_warm_access,
            expected(
                opcode,
                create_contexts,
                stack,
            ),
        )
        for opcode, callee_init_codes, create_contexts, stack, is_warm_access in product(
            opcodes, callee_init_codes, create_contexts, stacks, is_warm_accesss
        )
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "opcode, caller, callee_init_codes, caller_ctx, stack, is_warm_access, expected",
    TESTING_DATA,
)
def test_create_create2(
    opcode: Opcode,
    caller: Account,
    callee_init_codes: Bytecode,
    caller_ctx: CreateContext,
    stack: Stack,
    is_warm_access: bool,
    expected: Expected,
):
    randomness = rand_fq()

    is_create2 = 1 if opcode == Opcode.CREATE2 else 0
    if is_create2 == 1:
        caller_bytecode = (
            Bytecode()
            .mstore(stack.offset, callee_init_codes.code)
            .create2(
                stack.value,
                stack.offset,
                stack.size,
                stack.salt,
            )
            .stop()
        )
    else:  # CREATE
        caller_bytecode = (
            Bytecode()
            .mstore(stack.offset, callee_init_codes.code)
            .create(
                stack.value,
                stack.offset,
                stack.size,
            )
            .stop()
        )

    callee_bytecode = callee_init_codes
    callee_bytecode_hash = RLC(callee_bytecode.hash(), randomness)

    nonce = caller.nonce
    is_success = True if callee_init_codes is RETURN_BYTECODE else True
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

    contract_addr = keccak256(rlp.encode([caller.address.to_bytes(20, "big"), caller.nonce]))
    contract_address = int.from_bytes(contract_addr[-20:], "big")

    # can't be a static all
    is_static = 0

    call_id = 65
    rw_counter = call_id
    # CREATE: 33 * (3(push) + 2(push from mstore)) + 1(CREATE) + 1(mstore)
    # CREATE2: 33 * (4(push) + 2(push from mstore)) + 1(CREATE) + 1(mstore)
    next_program_counter = 33 * 6 + 1 + 1 if is_create2 else 33 * 5 + 1 + 1
    assert caller_bytecode.code[next_program_counter - 1] == Opcode.CREATE
    # CREATE: 1024 - 3 + 1 = 1022
    # CREATE2: 1024 - 4 + 1 = 1021
    stack_pointer = 1021 - is_create2

    rw_dictionary = RWDictionary(rw_counter)
    # fmt: off
    # stack
    if is_create2:
        rw_dictionary.stack_read(1, 1020, RLC(stack.salt, randomness))
    rw_dictionary \
        .stack_read(1, 1021, RLC(stack.value, randomness)) \
        .stack_read(1, 1022, RLC(stack.offset, randomness)) \
        .stack_read(1, 1023, RLC(stack.size, randomness)) \
        .stack_write(1, 1023, RLC(contract_address, randomness)) \

    # caller's call context
    rw_dictionary \
        .call_context_read(1, CallContextFieldTag.Depth, 1) \
        .call_context_read(1, CallContextFieldTag.TxId, 1) \
        .call_context_read(1, CallContextFieldTag.CallerAddress, caller.address) \
        .account_write(caller.address, AccountFieldTag.Nonce, nonce, nonce - 1) \
        .call_context_read(1, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(1, CallContextFieldTag.IsStatic, is_static) \
        .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, caller_ctx.rw_counter_end_of_reversion) \
        .call_context_read(1, CallContextFieldTag.IsPersistent, caller_ctx.is_persistent) \
        .tx_access_list_account_write(1, contract_address, True, is_warm_access, rw_counter_of_reversion=None if caller_ctx.is_persistent else caller_ctx.rw_counter_end_of_reversion - caller_ctx.reversible_write_counter) \
        .account_write(contract_address, AccountFieldTag.CodeHash, callee_bytecode_hash, 0) \
    
    # callee's reversion_info
    caller_balance_prev = RLC(caller.balance, randomness)
    callee_balance_prev = RLC(0, randomness)
    caller_balance = RLC(caller.balance - stack.value, randomness)
    callee_balance = RLC(stack.value, randomness)
    rw_dictionary \
        .call_context_read(call_id, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion) \
        .call_context_read(call_id, CallContextFieldTag.IsPersistent, callee_is_persistent)

    # For `transfer` invocation.
    rw_dictionary \
        .account_write(caller.address, AccountFieldTag.Balance, caller_balance, caller_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion) \
        .account_write(contract_address, AccountFieldTag.Balance, callee_balance, callee_balance_prev, rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion - 1)

    # copy_table
    src_data = dict(
        [
            (i, callee_bytecode.code[i] if i < len(callee_bytecode.code) else 0)
            for i in range(stack.offset, stack.offset+ stack.size)
        ]
    )
    copy_circuit = CopyCircuit().copy(
        randomness,
        rw_dictionary,
        1,
        CopyDataTypeTag.Memory,
        callee_bytecode_hash.expr(),
        CopyDataTypeTag.Bytecode,
        stack.offset,
        stack.offset + stack.size,
        0,
        stack.size,
        src_data,
    )
    # caller's call context
    rw_dictionary \
        .call_context_write(1, CallContextFieldTag.ProgramCounter, next_program_counter) \
        .call_context_write(1, CallContextFieldTag.StackPointer, 1023) \
        .call_context_write(1, CallContextFieldTag.GasLeft, expected.caller_gas_left) \
        .call_context_write(1, CallContextFieldTag.MemorySize, expected.next_memory_size) \
        .call_context_write(1, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter + 1) 
    
    # callee's call context
    rw_dictionary \
        .call_context_read(call_id, CallContextFieldTag.CallerId, 1) \
        .call_context_read(call_id, CallContextFieldTag.TxId, 1) \
        .call_context_read(call_id, CallContextFieldTag.Depth, 2) \
        .call_context_read(call_id, CallContextFieldTag.CallerAddress, caller.address) \
        .call_context_read(call_id, CallContextFieldTag.CalleeAddress, contract_address) \
        .call_context_read(call_id, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(call_id, CallContextFieldTag.IsStatic, is_static) \
        .call_context_read(call_id, CallContextFieldTag.IsRoot, False) \
        .call_context_read(call_id, CallContextFieldTag.IsCreate, False) \
        .call_context_read(call_id, CallContextFieldTag.CodeHash, RLC(EMPTY_CODE_HASH))
    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(
            chain(
                caller_bytecode.table_assignments(randomness),
                callee_bytecode.table_assignments(randomness),
                callee_init_codes.table_assignments(randomness),
            )
        ),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    # FIXME
    # verify_copy_table(copy_circuit, tables, randomness)

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CREATE,
                rw_counter=rw_counter,
                call_id=1,
                is_root=False,
                is_create=True,
                code_hash=RLC(caller_bytecode.hash(), randomness),
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
