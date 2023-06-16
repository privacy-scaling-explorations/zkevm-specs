import pytest
import rlp

from zkevm_specs.evm_circuit import (
    ExecutionState,
    StepState,
    CopyCircuit,
    verify_steps,
    Tables,
    AccountFieldTag,
    CallContextFieldTag,
    Block,
    Transaction,
    AccessTuple,
    Account,
    Bytecode,
    RWDictionary,
    CopyDataTypeTag,
)
from zkevm_specs.evm_circuit.typing import KeccakCircuit
from zkevm_specs.util import Word, EMPTY_CODE_HASH, U64, FQ
from common import rand_address, rand_range, rand_word, rand_fq
from zkevm_specs.util.hash import keccak256

RETURN_BYTECODE = Bytecode().return_(0, 0)
REVERT_BYTECODE = Bytecode().revert(0, 0)

CALLEE_ADDRESS = 0xFF
CALLEE_WITH_NOTHING = Account(address=CALLEE_ADDRESS)
CALLEE_WITH_RETURN_BYTECODE = Account(address=CALLEE_ADDRESS, code=RETURN_BYTECODE)
CALLEE_WITH_REVERT_BYTECODE = Account(address=CALLEE_ADDRESS, code=REVERT_BYTECODE)

CALL_ID = 1


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


TESTING_DATA = (
    # Transfer 1 ether to EOA, successfully
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, value=int(1e18)),
        CALLEE_WITH_NOTHING,
        True,
    ),
    # Transfer 1 ether to contract, successfully
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, value=int(1e18)),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer 1 ether to contract, tx reverts
    (
        Transaction(caller_address=0xFE, callee_address=CALLEE_ADDRESS, value=int(1e18)),
        CALLEE_WITH_REVERT_BYTECODE,
        False,
    ),
    # Transfer random ether, successfully
    (
        Transaction(
            caller_address=rand_address(), callee_address=CALLEE_ADDRESS, value=rand_range(1e20)
        ),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer nothing with random gas_price, successfully
    (
        Transaction(
            caller_address=rand_address(),
            callee_address=CALLEE_ADDRESS,
            gas_price=rand_range(42857142857143),
        ),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer random ether, tx reverts
    (
        Transaction(
            caller_address=rand_address(), callee_address=CALLEE_ADDRESS, value=rand_range(1e20)
        ),
        CALLEE_WITH_REVERT_BYTECODE,
        False,
    ),
    # Transfer nothing with random gas_price, tx reverts
    (
        Transaction(
            caller_address=rand_address(),
            callee_address=CALLEE_ADDRESS,
            gas_price=rand_range(42857142857143),
        ),
        CALLEE_WITH_REVERT_BYTECODE,
        False,
    ),
    # Transfer nothing with some calldata
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=21080,
            call_data=bytes([1, 2, 3, 4, 0, 0, 0, 0]),
        ),
        CALLEE_WITH_RETURN_BYTECODE,
        True,
    ),
    # Transfer with wrong nonce
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            value=int(1e18),
            nonce=U64(100),
            invalid_tx=1,
        ),
        CALLEE_WITH_NOTHING,
        True,  # is success because the tx is skipped
    ),
    # Transfer with insufficient balance
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=21080,
            value=int(1e21),
            invalid_tx=1,
        ),
        CALLEE_WITH_NOTHING,
        True,  # is success because the tx is skipped
    ),
    # Transfer with insufficient balance and ignore the revert code
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=21080,
            value=int(1e21),
            invalid_tx=1,
        ),
        CALLEE_WITH_REVERT_BYTECODE,
        True,  # is success because the tx is skipped
    ),
    # Transfer with sufficient intrinsic gas
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=21080 + 2400 + 1900 * 2,
            value=int(1e17),
            invalid_tx=0,
            access_list=[AccessTuple(address=0xFE, storage_keys=[rand_word(), rand_word()])],
        ),
        CALLEE_WITH_NOTHING,
        True,  # is success because the tx is skipped
    ),
    # Transfer with insufficient intrinsic gas
    (
        Transaction(
            caller_address=0xFE,
            callee_address=CALLEE_ADDRESS,
            gas=21080,
            value=int(1e17),
            invalid_tx=1,
            access_list=[AccessTuple(address=0xFE, storage_keys=[rand_word(), rand_word()])],
        ),
        CALLEE_WITH_NOTHING,
        True,  # is success because the tx is skipped
    ),
    # Create tx without initcode, without value
    (
        Transaction(
            caller_address=0xFE,
            callee_address=None,
            gas=100000,  # TODO(amb) make more precise gas
        ),
        CALLEE_WITH_NOTHING,
        True,
    ),
    # Create tx without initcode, with value
    (
        Transaction(
            caller_address=0xFE,
            callee_address=None,
            gas=100000,  # TODO(amb) make more precise gas
            value=1,
        ),
        CALLEE_WITH_NOTHING,
        True,
    ),
    # Create tx with initcode, no value
    (
        Transaction(
            caller_address=0xFE,
            callee_address=None,
            gas=53580,  # TODO(amb) make more precise gas
            call_data=bytes(gen_bytecode(True, 0, True).code),
        ),
        CALLEE_WITH_NOTHING,
        True,
    ),
    # Create tx with initcode and value
    (
        Transaction(
            caller_address=0xFE,
            callee_address=None,
            gas=53580,
            value=1,
            call_data=bytes(gen_bytecode(True, 0, True).code),
        ),
        CALLEE_WITH_NOTHING,
        True,
    ),
    # Create tx with reverting initcode
    (
        Transaction(
            caller_address=0xFE,
            callee_address=None,
            gas=53580,
            value=1,
            call_data=bytes(gen_bytecode(False, 0, True).code),
        ),
        CALLEE_WITH_NOTHING,
        True,
    ),
)


@pytest.mark.parametrize("tx, callee, is_success", TESTING_DATA)
def test_begin_tx(tx: Transaction, callee: Account, is_success: bool):
    randomness_keccak = rand_fq()

    is_tx_valid = 1 - tx.invalid_tx
    is_tx_create = tx.callee_address == None
    rw_counter_end_of_reversion = 24
    caller_nonce_prev = 0
    caller_balance_prev = int(1e20)
    callee_balance_prev = callee.balance
    caller_balance = (
        caller_balance_prev - (tx.value + tx.gas * tx.gas_price)
        if is_tx_valid
        else caller_balance_prev
    )
    callee_balance = callee_balance_prev + tx.value if is_tx_valid else callee_balance_prev

    calldata_hash = Word(int.from_bytes(keccak256(tx.call_data), "big"))
    bytecode_hash = calldata_hash if is_tx_create else Word(callee.code_hash())

    contract_address = keccak256(rlp.encode([tx.caller_address.to_bytes(20, "big"), tx.nonce]))
    contract_address = int.from_bytes(contract_address[-20:], "big")

    callee_address = contract_address if is_tx_create else tx.callee_address

    # fmt: off
    rw_dictionary = (
        RWDictionary(1)
        .call_context_read(1, CallContextFieldTag.TxId, tx.id)
        .call_context_read(1, CallContextFieldTag.RwCounterEndOfReversion, 0 if is_success else rw_counter_end_of_reversion)
        .call_context_read(1, CallContextFieldTag.IsPersistent, is_success)
        .call_context_read(1, CallContextFieldTag.IsSuccess, is_success)
        .account_write(tx.caller_address, AccountFieldTag.Nonce, caller_nonce_prev + is_tx_valid, caller_nonce_prev)
        .tx_access_list_account_write(tx.id, tx.caller_address, True, False)
        .tx_access_list_account_write(tx.id, callee_address, True, False)
        .account_write(tx.caller_address, AccountFieldTag.Balance, Word(caller_balance), Word(caller_balance_prev), rw_counter_of_reversion=None if is_success else rw_counter_end_of_reversion)
        .account_write(callee_address, AccountFieldTag.Balance, Word(callee_balance), Word(callee_balance_prev), rw_counter_of_reversion=None if is_success else rw_counter_end_of_reversion - 1)
    )

    is_create_tx_with_calldata = is_tx_create and len(tx.call_data)>0
    is_regular_tx_with_code_hash = not is_tx_create and callee.code_hash() != EMPTY_CODE_HASH

    copy_table = CopyCircuit().rows
    keccak_table = KeccakCircuit().rows

    if not is_tx_create:
       rw_dictionary \
       .account_read(tx.callee_address, AccountFieldTag.CodeHash, bytecode_hash)
    elif len(tx.call_data)>0:

        src_data_dict = dict([(i, tx.call_data[i]) for i in range(len(tx.call_data))])

        copy_calldata_to_keccak = CopyCircuit().copy(
            randomness_keccak,
            rw_dictionary,
            1, # TX_ID
            CopyDataTypeTag.TxCalldata,
            CALL_ID,
            CopyDataTypeTag.RlcAcc,
            FQ.zero(),
            len(tx.call_data),
            FQ.zero(),
            len(tx.call_data),
            src_data_dict,
        )

        src_data_bytecode_dict = dict(
            [
                (i, (Bytecode(tx.call_data).code[i], Bytecode(tx.call_data).is_code[i]))
                for i in range(len(Bytecode(tx.call_data).code))
            ]
        )

        copy_calldata_to_bytecode = CopyCircuit().copy(
            randomness_keccak,
            rw_dictionary,
            1, # TX_ID
            CopyDataTypeTag.TxCalldata,
            calldata_hash,
            CopyDataTypeTag.Bytecode,
            FQ.zero(),
            len(tx.call_data),
            FQ.zero(),
            len(tx.call_data),
            src_data_bytecode_dict,
        )

        copy_table = copy_calldata_to_keccak.rows + copy_calldata_to_bytecode.rows

        keccak_table = KeccakCircuit().add(
            tx.call_data,
            randomness_keccak
        ).rows


    if (is_create_tx_with_calldata or is_regular_tx_with_code_hash) and is_tx_valid == 1:
        rw_dictionary \
        .call_context_read(1, CallContextFieldTag.Depth, 1) \
        .call_context_read(1, CallContextFieldTag.CallerAddress, Word(tx.caller_address)) \
        .call_context_read(1, CallContextFieldTag.CalleeAddress, Word(callee_address)) \
        .call_context_read(1, CallContextFieldTag.CallDataOffset, 0) \
        .call_context_read(1, CallContextFieldTag.CallDataLength, len(tx.call_data)) \
        .call_context_read(1, CallContextFieldTag.Value, Word(tx.value)) \
        .call_context_read(1, CallContextFieldTag.IsStatic, is_tx_create) \
        .call_context_read(1, CallContextFieldTag.LastCalleeId, 0) \
        .call_context_read(1, CallContextFieldTag.LastCalleeReturnDataOffset, 0) \
        .call_context_read(1, CallContextFieldTag.LastCalleeReturnDataLength, 0) \
        .call_context_read(1, CallContextFieldTag.IsRoot, True) \
        .call_context_read(1, CallContextFieldTag.IsCreate, is_tx_create) \
        .call_context_read(1, CallContextFieldTag.CodeHash, bytecode_hash)

    # fmt: on

    tables = Tables(
        block_table=set(Block().table_assignments()),
        tx_table=set(tx.table_assignments()),
        bytecode_table=set(callee.code.table_assignments()),
        rw_table=set(rw_dictionary.rws),
        copy_circuit=copy_table,
        keccak_table=keccak_table,
    )

    verify_steps(
        tables=tables,
        steps=[
            StepState(
                execution_state=ExecutionState.BeginTx,
                rw_counter=1,
            ),
            StepState(
                execution_state=ExecutionState.EndTx
                if callee.code_hash() == EMPTY_CODE_HASH or is_tx_valid == 0
                else ExecutionState.PUSH,
                rw_counter=rw_dictionary.rw_counter,
                call_id=CALL_ID,
                is_root=True,
                is_create=is_tx_create,
                code_hash=bytecode_hash,
                program_counter=0,
                stack_pointer=1024,
                gas_left=0,
                reversible_write_counter=2,
            ),
        ],
        begin_with_first_step=True,
    )
