import pytest

from zkevm_specs.evm import (
    ExecutionState,
    StepState,
    verify_steps,
    Tables,
    RWTableTag,
    RW,
    Block,
    Bytecode,
    CallContextFieldTag,
    AccountFieldTag,
    RWDictionary,
)
from zkevm_specs.util import (
    rand_address,
    rand_range,
    rand_word,
    rand_fq,
    U256,
    U160,
    keccak256,
    RLC,
    rand_bytes,
)
from zkevm_specs.util.param import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS, GAS_COST_WARM_ACCESS
from zkevm_specs.util.hash import EMPTY_CODE_HASH


TESTING_DATA = [
    (0x30000, 0, 0, bytes(), True),  # warm empty account
    (0x30000, 0, 0, bytes(), False),  # cold empty account
    (0x30000, 1, 200, bytes([10, 40]), True),  # warm non-empty account
    (0x30000, 1, 200, bytes([10, 10]), False),  # cold non-empty account
    (0x30000, 1, 0, bytes(), False),  # non-empty account because of nonce
    (rand_address(), rand_word(), rand_word(), rand_bytes(100), rand_range(2) == 0),
]


@pytest.mark.parametrize("address, nonce, balance, code, is_warm", TESTING_DATA)
def test_extcodehash(address: U160, nonce: U256, balance: U256, code: bytes, is_warm: bool):
    randomness = rand_fq()

    code_hash = int.from_bytes(keccak256(code), "big")
    result = 0 if (nonce == 0 and balance == 0 and code_hash == EMPTY_CODE_HASH) else code_hash

    tx_id = 1
    call_id = 1

    rw_table = set(
        RWDictionary(0)
        .stack_read(call_id, 1023, RLC(address, randomness))
        .call_context_read(tx_id, CallContextFieldTag.TxId, tx_id)
        .tx_access_list_account_write(tx_id, address, True, is_warm)
        .account_read(address, AccountFieldTag.Nonce, RLC(nonce, randomness))
        .account_read(address, AccountFieldTag.Balance, RLC(balance, randomness))
        .account_read(address, AccountFieldTag.CodeHash, RLC(code_hash, randomness))
        .stack_write(call_id, 1023, RLC(result, randomness))
        .rws
    )

    bytecode = Bytecode().extcodehash()
    tables = Tables(
        block_table=Block(),
        tx_table=set(),
        bytecode_table=set(bytecode.table_assignments(randomness)),
        rw_table=rw_table,
    )

    bytecode_hash = RLC(bytecode.hash(), randomness)
    verify_steps(
        randomness=randomness,
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.EXTCODEHASH,
                rw_counter=0,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=0,
                stack_pointer=1023,
                gas_left=GAS_COST_WARM_ACCESS + (not is_warm) * EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
            ),
            StepState(
                execution_state=ExecutionState.STOP,
                rw_counter=7,
                call_id=1,
                is_root=True,
                is_create=False,
                code_source=bytecode_hash,
                program_counter=1,
                stack_pointer=1023,
                gas_left=0,
            ),
        ],
    )
