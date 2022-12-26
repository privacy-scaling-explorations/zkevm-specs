import pytest
from itertools import chain
from zkevm_specs.copy_circuit import verify_copy_table
from zkevm_specs.evm import (
    verify_steps,
    Tables,
    Block,
    Bytecode,
    ExecutionState,
    StepState,
    Opcode,
    U64,
    U160,
    RLC,
    CopyCircuit,
    CopyDataTypeTag,
    AccountFieldTag,
    CallContextFieldTag,
)
from zkevm_specs.evm.typing import RWDictionary
from zkevm_specs.util import (
    rand_bytes,
    rand_fq,
    keccak256,
    EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_COPY,
    memory_word_size,
    memory_expansion,
)


TESTING_DATA = (
    # empty code
    (bytes(), True, True, 1, 0x30000, 0x00, 0x00, 54),  # warm account
    (bytes(), False, True, 1, 0x30000, 0x00, 0x00, 54),  # cold account
    # non-empty code
    (bytes([10, 40]), True, True, 1, 0x30000, 0x00, 0x00, 54),  # warm account
    (bytes([10, 10]), False, True, 1, 0x30000, 0x00, 0x00, 54),  # cold account
    # code length > 256
    (rand_bytes(256), True, True, 1, 0x30000, 0x00, 0x00, 54),  # warm account
    (rand_bytes(256), False, True, 1, 0x30000, 0x00, 0x00, 54),  # cold account
    # out of bound cases
    (rand_bytes(64), True, True, 1, 0x30000, 0x20, 0x00, 260),  # warm account
    (rand_bytes(64), False, True, 1, 0x30000, 0x20, 0x00, 260),  # cold account
    # non-existing account
    (bytes(), True, True, 0, 0x30000, 0x00, 0x00, 54),  # warm account
    (bytes(), False, True, 0, 0x30000, 0x00, 0x00, 54),  # cold account
    # non-existing account & code length > 256
    (rand_bytes(256), True, True, 0, 0x30000, 0x00, 0x00, 54),  # warm account
    (rand_bytes(256), False, True, 0, 0x30000, 0x00, 0x00, 54),  # cold account
    # non-existing account  & non-empty code
    (bytes([10, 40]), True, True, 0, 0x30000, 0x00, 0x00, 54),  # warm account
    (bytes([10, 10]), False, True, 0, 0x30000, 0x00, 0x00, 54),  # cold account
    #  non-existing account  & out of bound cases
    (rand_bytes(64), True, True, 0, 0x30000, 0x20, 0x00, 260),  # warm account
    (rand_bytes(64), False, True, 0, 0x30000, 0x20, 0x00, 260),  # cold account
)


@pytest.mark.parametrize(
    "code, is_warm, is_persistent, exists, address, src_addr, dst_addr, length", TESTING_DATA
)
def test_extcodecopy(
    code: bytes,
    is_warm: bool,
    is_persistent: bool,
    exists: int,
    address: U160,
    src_addr: U64,
    dst_addr: U64,
    length: U64,
):
    randomness = rand_fq()
    code = code if exists == 1 else bytes()
    code_hash = int.from_bytes(keccak256(code), "big")

    next_memory_word_size = memory_word_size(dst_addr + length)
    _, memory_expansion_cost = memory_expansion(0, dst_addr + length if length else 0)
    memory_gas_cost = memory_expansion_cost + memory_word_size(length) * GAS_COST_COPY

    gas_cost_extcodecopy = (
        Opcode.EXTCODECOPY.constant_gas_cost()
        + memory_gas_cost
        + (not is_warm) * EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS
    )

    tx_id = 2
    call_id = 3

    rw_counter_end_of_reversion = 0 if is_persistent else 9
    reversible_write_counter = 0

    rw_dictionary = (
        RWDictionary(1)
        .stack_read(call_id, 1020, RLC(address, randomness))
        .stack_read(call_id, 1021, RLC(dst_addr, randomness))
        .stack_read(call_id, 1022, RLC(src_addr, randomness))
        .stack_read(call_id, 1023, RLC(length, randomness))
        .call_context_read(call_id, CallContextFieldTag.TxId, tx_id)
        .call_context_read(
            call_id, CallContextFieldTag.RwCounterEndOfReversion, rw_counter_end_of_reversion
        )
        .call_context_read(call_id, CallContextFieldTag.IsPersistent, is_persistent)
        .tx_access_list_account_write(
            tx_id,
            address,
            True,
            is_warm,
            rw_counter_of_reversion=rw_counter_end_of_reversion - reversible_write_counter,
        )
    )
    if exists == 1:
        rw_dictionary.account_read(address, AccountFieldTag.CodeHash, RLC(code_hash, randomness))
    else:
        rw_dictionary.account_read(
            address, AccountFieldTag.NonExisting, RLC(1 - exists, randomness)
        )

    bytecode = Bytecode().extcodecopy()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    steps = [
        StepState(
            execution_state=ExecutionState.EXTCODECOPY,
            rw_counter=1,
            call_id=call_id,
            is_root=True,
            code_hash=bytecode_hash,
            program_counter=0,
            stack_pointer=1020,
            gas_left=gas_cost_extcodecopy,
            aux_data=exists,
        )
    ]

    # rw counter before memory writes
    rw_counter_interim = rw_dictionary.rw_counter

    src_data = dict(
        [
            (i, (Bytecode(code).code[i], Bytecode(code).is_code[i]))
            for i in range(len(Bytecode(code).code))
        ]
    )
    result = RLC(code_hash, randomness).rlc_value if exists == 1 else RLC(0, randomness).rlc_value
    copy_circuit = CopyCircuit().copy(
        randomness,
        rw_dictionary,
        result,
        CopyDataTypeTag.Bytecode,
        call_id,
        CopyDataTypeTag.Memory,
        src_addr,
        len(Bytecode(code).code),
        dst_addr,
        length,
        src_data,
    )

    # rw counter post memory writes
    rw_counter_final = rw_dictionary.rw_counter
    assert rw_counter_final - rw_counter_interim == length

    steps.append(
        StepState(
            execution_state=ExecutionState.STOP if is_persistent else ExecutionState.REVERT,
            rw_counter=rw_dictionary.rw_counter,
            call_id=call_id,
            is_root=True,
            code_hash=bytecode_hash,
            program_counter=1,
            stack_pointer=1024,
            memory_size=next_memory_word_size,
            gas_left=0,
        )
    )
    tables = Tables(
        block_table=Block(),
        tx_table=set(),
        bytecode_table=set(
            chain(
                bytecode.table_assignments(randomness),
                Bytecode(code).table_assignments(randomness),
            )
        ),
        rw_table=rw_dictionary.rws,
        copy_circuit=copy_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables, randomness)

    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=steps,
    )
