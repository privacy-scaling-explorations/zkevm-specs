import pytest
import rlp
from collections import namedtuple
from itertools import chain, product
from common import rand_fq
from zkevm_specs.copy_circuit import verify_copy_table
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
from zkevm_specs.util.hash import EMPTY_CODE_HASH, keccak256
from zkevm_specs.util.param import GAS_COST_COPY_SHA3, GAS_COST_CREATE
from zkevm_specs.util import Word

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


CALLER = Account(address=0xFE, balance=int(1e20), nonce=10)


def gen_bytecode(is_return: bool, offset: int, has_init_code: bool) -> Bytecode:
    if not has_init_code:
        return Bytecode()

    """Generate bytecode that has 64 bytes of memory initialized and returns with `offset` and `length`"""
    bytecode = (
        Bytecode()
        .push(0x2222222222222222222222222222222222222222222222222222222222222222, n_bytes=32)
        .push(offset, n_bytes=1)
        .mstore()
    )

    if is_return:
        bytecode.return_()
    else:
        bytecode.revert()

    return bytecode


def calc_gas_cost(
    opcode: Opcode,
    caller_ctx: CreateContext,
    stack: Stack,
):
    def memory_size(offset: int, length: int) -> int:
        if length == 0:
            return 0
        return (offset + length + 31) // 32

    is_create2 = 1 if opcode == Opcode.CREATE2 else 0

    offset = stack.offset
    size = stack.size

    next_memory_size = max(
        memory_size(offset, size),
        caller_ctx.memory_word_size,
    )
    memory_expansion_gas_cost = (
        next_memory_size * next_memory_size
        - caller_ctx.memory_word_size * caller_ctx.memory_word_size
    ) // 512 + 3 * (next_memory_size - caller_ctx.memory_word_size)

    # GAS_COST_CODE_DEPOSIT * (bytecode size) is not included here, it should be `return_revert``
    # extra gas cost for CREATE2
    gas_cost = GAS_COST_CREATE + memory_expansion_gas_cost
    if is_create2 == 1:
        gas_cost += GAS_COST_COPY_SHA3 * memory_size(0, size)
    gas_available = caller_ctx.gas_left - gas_cost
    all_but_one_64th_gas = gas_available - gas_available // 64
    callee_gas_left = min(all_but_one_64th_gas, caller_ctx.gas_left)
    caller_gas_left = caller_ctx.gas_left - (gas_cost + callee_gas_left)

    return (
        caller_gas_left,
        callee_gas_left,
        gas_cost,
        next_memory_size,
    )


def gen_testing_data():
    opcodes = [
        Opcode.CREATE,
        Opcode.CREATE2,
    ]
    is_return = [
        True,
        False,
    ]
    create_contexts = [
        CreateContext(gas_left=1_000_000, is_persistent=True),
        CreateContext(gas_left=1_000_000, is_persistent=False, rw_counter_end_of_reversion=80),
    ]
    stacks = [
        Stack(value=int(1e18), offset=64, salt=int(12345)),
        Stack(value=int(1e25), offset=64),
    ]
    stack_depth = [1, 1024, 1025]
    is_warm_accesss = [True, False]
    has_init_code = [True, False]

    return [
        (
            opcode,
            CALLER,
            is_return,
            create_contexts,
            stack,
            stack_depth,
            is_warm_access,
            has_init_code,
        )
        for opcode, is_return, create_contexts, stack, stack_depth, is_warm_access, has_init_code in product(
            opcodes, is_return, create_contexts, stacks, stack_depth, is_warm_accesss, has_init_code
        )
    ]


TESTING_DATA = gen_testing_data()


@pytest.mark.parametrize(
    "opcode, caller, is_return, caller_ctx, stack, stack_depth, is_warm_access, has_init_code",
    TESTING_DATA,
)
def test_create_create2(
    opcode: Opcode,
    caller: Account,
    is_return: bool,
    caller_ctx: CreateContext,
    stack: Stack,
    stack_depth: int,
    is_warm_access: bool,
    has_init_code: bool,
):
    randomness_keccak = rand_fq()
    CURRENT_CALL_ID = 1

    init_codes = gen_bytecode(is_return, stack.offset, has_init_code)
    stack = stack._replace(size=len(init_codes.code))
    init_codes_hash = Word(init_codes.hash())

    init_bytecode = gen_bytecode(is_return, stack.offset, has_init_code)
    is_create2 = 1 if opcode == Opcode.CREATE2 else 0
    if is_create2 == 1:
        caller_bytecode = init_bytecode.create2(
            stack.value,
            stack.offset,
            stack.size,
            stack.salt,
        ).stop()
    else:  # CREATE
        caller_bytecode = init_bytecode.create(
            stack.value,
            stack.offset,
            stack.size,
        ).stop()

    caller_bytecode_hash = Word(caller_bytecode.hash())
    (caller_gas_left, callee_gas_left, gas_cost, next_memory_size) = calc_gas_cost(
        opcode,
        caller_ctx,
        stack,
    )

    nonce = caller.nonce
    is_success = is_return
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

    if is_create2 == 1:
        preimage = (
            b"\xff"
            + caller.address.to_bytes(20, "big")
            + int(stack.salt).to_bytes(32, "little")
            + init_codes_hash.int_value().to_bytes(32, "little")
        )
        contract_addr = keccak256(preimage)
    else:
        contract_addr = keccak256(rlp.encode([caller.address.to_bytes(20, "big"), caller.nonce]))
    contract_address = int.from_bytes(contract_addr[-20:], "big")

    # can't be a static all
    is_static = 0

    next_call_id = 66
    rw_counter = next_call_id

    # CREATE: 33 * 3(push) + 1(CREATE) + 1(mstore) + 33(PUSH32) + 2(PUSH) + 1(RETURN)
    # CREATE2: 33 * 4(push) + 1(CREATE2) + 1(mstore) + 33(PUSH32) + 2(PUSH) + 1(RETURN)
    pc = 33 * 4 + 1 if is_create2 else 33 * 3 + 1
    if has_init_code:
        next_program_counter = pc + 1 + 35 + 1 if is_create2 else pc + 1 + 35 + 1
    else:
        next_program_counter = pc
    assert caller_bytecode.code[next_program_counter - 1] == opcode

    # CREATE: 1024 - 3 + 1 = 1022
    # CREATE2: 1024 - 4 + 1 = 1021
    stack_pointer = 1021 - is_create2

    # caller and callee balance
    caller_balance_prev = caller.balance
    callee_balance_prev = 0
    caller_balance = caller_balance_prev - stack.value
    callee_balance = callee_balance_prev + stack.value

    is_precheck_ok = (
        (caller_balance >= stack.value) and (nonce > nonce - 1) and (stack_depth <= 1024)
    )

    src_data = dict(
        [
            (
                i,
                (
                    init_codes.code[i - stack.offset],
                    init_codes.is_code[i - stack.offset],
                )
                if i - stack.offset < len(init_codes.code)
                else (0, 0),
            )
            for i in range(stack.offset, stack.offset + stack.size)
        ]
    )

    # fmt: off
    # stack
    rw_dictionary = (
        RWDictionary(rw_counter)
        .stack_read(CURRENT_CALL_ID, 1021 - is_create2, Word(stack.value))
        .stack_read(CURRENT_CALL_ID, 1022 - is_create2, Word(stack.offset))
        .stack_read(CURRENT_CALL_ID, 1023 - is_create2, Word(stack.size))
    )
    if is_create2:
        rw_dictionary.stack_read(CURRENT_CALL_ID, 1023, Word(stack.salt))   
    rw_dictionary.stack_write(CURRENT_CALL_ID, 1023, Word(contract_address) if is_success else Word(0))

    # caller's call context
    rw_dictionary \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.Depth, stack_depth) \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.TxId, 1) \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.CallerAddress, caller.address) \
        .account_write(caller.address, AccountFieldTag.Nonce, nonce, nonce - 1) \
        .account_write(caller.address, AccountFieldTag.Balance, caller_balance, caller_balance_prev) \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.IsSuccess, is_success) \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.IsStatic, is_static) \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.RwCounterEndOfReversion, caller_ctx.rw_counter_end_of_reversion) \
        .call_context_read(CURRENT_CALL_ID, CallContextFieldTag.IsPersistent, caller_ctx.is_persistent)
        
    if is_precheck_ok:
        rw_dictionary \
            .tx_access_list_account_write(CURRENT_CALL_ID, contract_address, True, is_warm_access, rw_counter_of_reversion=None if caller_ctx.is_persistent else caller_ctx.rw_counter_end_of_reversion - caller_ctx.reversible_write_counter) \
            .account_write(contract_address, AccountFieldTag.CodeHash, Word(EMPTY_CODE_HASH), 0)

        # callee's reversion_info
        rw_dictionary \
            .call_context_read(next_call_id, CallContextFieldTag.RwCounterEndOfReversion, callee_rw_counter_end_of_reversion) \
            .call_context_read(next_call_id, CallContextFieldTag.IsPersistent, callee_is_persistent)

        # For `transfer` invocation.
        rw_dictionary \
            .account_write(caller.address, AccountFieldTag.Balance, Word(caller_balance), Word(caller_balance_prev), rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion) \
            .account_write(contract_address, AccountFieldTag.Balance, Word(callee_balance), Word(callee_balance_prev), rw_counter_of_reversion=None if callee_is_persistent else callee_rw_counter_end_of_reversion - 1)
      
    if has_init_code and is_precheck_ok:
         # copy_table
        copy_circuit = CopyCircuit().copy(
            randomness_keccak,
            rw_dictionary,
            CURRENT_CALL_ID,
            CopyDataTypeTag.Memory,
            init_codes_hash,
            CopyDataTypeTag.Bytecode,
            stack.offset,
            stack.offset + stack.size,
            0,
            stack.size,
            src_data,
        )

        # caller's call context
        rw_dictionary \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.ProgramCounter, next_program_counter) \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.StackPointer, 1023) \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.GasLeft, caller_gas_left) \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.MemorySize, next_memory_size) \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.ReversibleWriteCounter, caller_ctx.reversible_write_counter + 1) 
 
        # callee's call context
        rw_dictionary \
            .call_context_read(next_call_id, CallContextFieldTag.CallerId, CURRENT_CALL_ID) \
            .call_context_read(next_call_id, CallContextFieldTag.TxId, 1) \
            .call_context_read(next_call_id, CallContextFieldTag.Depth, stack_depth+1) \
            .call_context_read(next_call_id, CallContextFieldTag.CallerAddress, caller.address) \
            .call_context_read(next_call_id, CallContextFieldTag.CalleeAddress, contract_address) \
            .call_context_read(next_call_id, CallContextFieldTag.IsSuccess, is_success) \
            .call_context_read(next_call_id, CallContextFieldTag.IsStatic, is_static) \
            .call_context_read(next_call_id, CallContextFieldTag.IsRoot, False) \
            .call_context_read(next_call_id, CallContextFieldTag.IsCreate, True) \
            .call_context_read(next_call_id, CallContextFieldTag.CodeHash, Word(EMPTY_CODE_HASH))
    

        tables = Tables(
            block_table=set(Block().table_assignments()),
            tx_table=set(),
            bytecode_table=set(
                chain(
                    caller_bytecode.table_assignments(),
                    init_codes.table_assignments(),
                )
            ),
            rw_table=set(rw_dictionary.rws),
            copy_circuit=copy_circuit.rows,
        )
        verify_copy_table(copy_circuit, tables, randomness_keccak)
     
    else:
        # caller's call context
        rw_dictionary \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.LastCalleeId, 0) \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
            .call_context_write(CURRENT_CALL_ID, CallContextFieldTag.LastCalleeReturnDataLength, 0)
        
        tables = Tables(
            block_table=set(Block().table_assignments()),
            tx_table=set(),
            bytecode_table=set(
                chain(
                    caller_bytecode.table_assignments(),
                    init_codes.table_assignments(),
                )
            ),
            rw_table=set(rw_dictionary.rws),)
    # fmt: on

    reversible_write_counter = caller_ctx.reversible_write_counter + (3 if is_precheck_ok else 1)
    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.CREATE2
                if is_create2 == 1
                else ExecutionState.CREATE,
                rw_counter=rw_counter,
                call_id=CURRENT_CALL_ID,
                is_root=False,
                is_create=True,
                code_hash=caller_bytecode_hash,
                program_counter=next_program_counter - 1,
                stack_pointer=stack_pointer,
                gas_left=caller_ctx.gas_left,
                memory_word_size=caller_ctx.memory_word_size,
                reversible_write_counter=caller_ctx.reversible_write_counter,
            ),
            (
                StepState(
                    execution_state=ExecutionState.PUSH,
                    rw_counter=rw_dictionary.rw_counter,
                    call_id=next_call_id,
                    is_root=False,
                    is_create=True,
                    code_hash=init_codes_hash,
                    program_counter=0,
                    stack_pointer=1024,
                    gas_left=callee_gas_left,
                    reversible_write_counter=2,
                )
                if has_init_code and is_precheck_ok
                else StepState(
                    execution_state=ExecutionState.PUSH,
                    rw_counter=rw_dictionary.rw_counter,
                    call_id=CURRENT_CALL_ID,
                    is_root=False,
                    is_create=True,
                    code_hash=caller_bytecode_hash,
                    program_counter=next_program_counter,
                    stack_pointer=1023,
                    gas_left=caller_ctx.gas_left - gas_cost,
                    reversible_write_counter=reversible_write_counter,
                )
            ),
        ],
    )
