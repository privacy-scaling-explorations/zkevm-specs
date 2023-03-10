import pytest


from zkevm_specs.evm import (
    GAS_COST_EXP_PER_BYTE,
    Block,
    Bytecode,
    ExecutionState,
    ExpCircuit,
    Opcode,
    RWDictionary,
    StepState,
    Tables,
    verify_steps,
)
from zkevm_specs.exp_circuit import verify_exp_circuit
from zkevm_specs.util import (
    byte_size,
    rand_fq,
    Word,
)


CALL_ID = 1
POW2 = 2**256
TESTING_DATA = (
    (0, 0),
    (0, POW2 - 1),
    (1, 0),
    (1, POW2 - 1),
    (0xCAFE, 0),
    (POW2 - 1, 0),
    (0, 1),
    (1, 1),
    (0xCAFE, 1),
    (POW2 - 1, 1),
    (2, 5),
    (3, 101),
    (5, 259),
    (7, 1023),
    (POW2 - 1, 2),
    (POW2 - 1, 3),
    (POW2 - 1, POW2 - 1),
)


@pytest.mark.parametrize("base, exponent", TESTING_DATA)
def test_exp(base: int, exponent: int):
    exponentiation = pow(base, exponent, POW2)

    bytecode = Bytecode().push(exponent, n_bytes=32).push(base, n_bytes=32).exp().stop()
    bytecode_hash = Word(bytecode.hash())

    base = Word(base)
    exponent = Word(exponent)
    exponentiation = Word(exponentiation)

    rw_dict = (
        RWDictionary(1)
        .stack_write(CALL_ID, 1023, exponent)
        .stack_write(CALL_ID, 1022, base)
        .stack_read(CALL_ID, 1022, base)
        .stack_read(CALL_ID, 1023, exponent)
        .stack_write(CALL_ID, 1023, exponentiation)
    )

    exp_circuit = ExpCircuit().add_event(base.int_value(), exponent.int_value(), rw_dict.rw_counter)

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments()),
        rw_table=set(rw_dict.rws),
        exp_circuit=exp_circuit.rows,
    )

    verify_exp_circuit(exp_circuit)

    gas = Opcode.EXP.constant_gas_cost() + byte_size(exponent.int_value()) * GAS_COST_EXP_PER_BYTE
    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EXP,
                rw_counter=3,
                call_id=CALL_ID,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=66,
                stack_pointer=1022,
                gas_left=gas,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=rw_dict.rw_counter,
                call_id=CALL_ID,
                is_root=True,
                is_create=False,
                code_hash=bytecode_hash,
                program_counter=67,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
