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
    RLC,
    # hi
    word_to_lo_hi,
    word_to_64s,
)


CALL_ID = 1
POW2 = 2**256
TESTING_DATA = (
    (0, 0),
    (1, 0),
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
)


@pytest.mark.parametrize("base, exponent", TESTING_DATA)
def test_exp(base: int, exponent: int):
    randomness = rand_fq()

    exponentiation = (base**exponent) % POW2

    bytecode = Bytecode().push(exponent, n_bytes=32).push(base, n_bytes=32).exp().stop()
    bytecode_hash = RLC(bytecode.hash(), randomness)

    base_rlc = RLC(base, randomness, n_bytes=32)
    exponent_rlc = RLC(exponent, randomness, n_bytes=32)
    exponentiation_rlc = RLC(exponentiation, randomness, n_bytes=32)

    rw_dict = (
        RWDictionary(1)
        .stack_write(CALL_ID, 1023, exponent_rlc)
        .stack_write(CALL_ID, 1022, base_rlc)
        .stack_read(CALL_ID, 1022, base_rlc)
        .stack_read(CALL_ID, 1023, exponent_rlc)
        .stack_write(CALL_ID, 1023, exponentiation_rlc)
    )

    exp_circuit = ExpCircuit().add_event(base, exponent, randomness, rw_dict.rw_counter)

    tables = Tables(
        block_table=set(Block().table_assignments(randomness)),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=set(rw_dict.rws),
        exp_circuit=exp_circuit.rows,
    )

    verify_exp_circuit(exp_circuit)

    gas = Opcode.EXP.constant_gas_cost() + byte_size(exponent) * GAS_COST_EXP_PER_BYTE
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
