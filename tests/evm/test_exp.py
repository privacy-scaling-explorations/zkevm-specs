import pytest

from zkevm_specs.evm import (
    Block,
    Bytecode,
    CopyCircuit,
    CopyDataTypeTag,
    ExecutionState,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.copy_circuit import verify_copy_table
from zkevm_specs.util import (
    byte_size,
    rand_fq,
    rand_range,
    FQ,
    GAS_COST_EXP,
    RLC,
)


CALL_ID = 1
TESTING_DATA = (
    (0x03, 0x04),
    (0x05, 0x101),
    (0x101, 0x202),
    (rand_range(2**64), rand_range(256)),
)


@pytest.mark.parametrize("base, exponent", TESTING_DATA)
def test_exp(base: int, exponent: int):
    randomness = rand_fq()

    bytecode = Bytecode().push(exponent, n_bytes=32).push(base, n_bytes=32).exp().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)
    pc_exp = 66

    base_rlc = RLC(base, randomness)
    exponent_rlc = RLC(exponent, randomness)
    exp = FQ(base) ** exponent
    exp_rlc = RLC(exp.n, randomness)

    rw_dictionary = (
        RWDictionary(1)
        .stack_write(CALL_ID, 1023, exponent_rlc)
        .stack_write(CALL_ID, 1022, base_rlc)
        .stack_read(CALL_ID, 1022, base_rlc)
        .stack_read(CALL_ID, 1023, exponent_rlc)
        .stack_write(CALL_ID, 1023, exp_rlc)
    )
    rw_counter_interim = rw_dictionary.rw_counter

    data = dict([(i, base) for i in range(0, exponent)])
    copy_circuit = CopyCircuit().copy(
        randomness,
        rw_dictionary,
        CALL_ID,
        CopyDataTypeTag.Exp,
        CALL_ID,
        CopyDataTypeTag.Exp,
        FQ.zero(),
        exponent,
        FQ.zero(),
        exponent,
        data,
    )
    assert rw_dictionary.rw_counter == rw_counter_interim

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_circuit.rows,
    )

    verify_copy_table(copy_circuit, tables, randomness)

    gas = Opcode.EXP.constant_gas_cost() + (GAS_COST_EXP * byte_size(exponent))
    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EXP,
                rw_counter=3,
                call_id=CALL_ID,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc_exp,
                stack_pointer=1022,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dictionary.rw_counter,
                call_id=CALL_ID,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=pc_exp + 1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
