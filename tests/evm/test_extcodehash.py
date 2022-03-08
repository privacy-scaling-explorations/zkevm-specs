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
)
from zkevm_specs.util import (
    rand_address,
    rand_range,
    rand_word,
    rand_fp,
    U256,
    U160,
    keccak256,
    RLC,
    rand_bytes,
)
from zkevm_specs.util.param import N_BYTES_WORD

TESTING_DATA = [
    (0x30000, 0, 0, bytes(), True),  # warm empty account
    (0x30000, 0, 0, bytes(), False),  # cold empty account
    (0x30000, 1, 200, bytes([10, 40]), True),  # warm non-empty account
    (0x30000, 1, 200, bytes([10, 10]), False),  # cold non-empty account
    (rand_address(), rand_word(), rand_word(), rand_bytes(100), rand_range(2) == 0),
]


@pytest.mark.parametrize("address, nonce, balance, code, is_warm", TESTING_DATA)
def test_extcodehash(address: U160, nonce: U256, balance: U256, code: bytes, is_warm: bool):
    randomness = rand_fp()

    bytecode = Bytecode().extcodehash()

    code_hash = int.from_bytes(keccak256(code), "big")
    result = 0 if (address == 0 and nonce == 0 and code_hash == keccak256("")) else code_hash
    rlc_code_hash = RLC(code_hash, randomness)

    rw_table = {
        (0, RW.Read, RWTableTag.Stack, 1, 1023, 0, address, 0, 0, 0),
        (1, RW.Read, RWTableTag.CallContext, 1, CallContextFieldTag.TxId, 0, 1, 0, 0, 0),
        (2, RW.Write, RWTableTag.TxAccessListAccount, 1, address, 0, 1, int(is_warm), 0, 0),
        (3, RW.Read, RWTableTag.Account, address, AccountFieldTag.Nonce, 0, nonce, 0, 0, 0),
        (4, RW.Read, RWTableTag.Account, address, AccountFieldTag.Balance, 0, balance, 0, 0, 0),
        (5, RW.Read, RWTableTag.Account, address, AccountFieldTag.CodeHash, 0, code_hash, 0, 0, 0),
        (6, RW.Write, RWTableTag.Stack, 1, 1023, 0, result, 0, 0, 0),
    }

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
                gas_left=100,
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
