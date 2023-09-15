from typing import Union, List, Tuple
import rlp  # type: ignore
from zkevm_specs.withdrawal_circuit import *
from zkevm_specs.util import FQ, U64
from common import rand_fq
from random import randrange
from eth_utils import keccak

keccak_randomness = rand_fq()
r = keccak_randomness


def verify(
    withdrawals_or_witness: Union[List[Withdrawal], Witness],
    MAX_WITHDRAWALS: int,
    success: bool = True,
):
    """
    Verify the circuit with the assigned witness (or the witness calculated
    from the withdrawals).  If `success` is False, expect the verification to
    fail.
    """
    witness = withdrawals_or_witness
    if isinstance(withdrawals_or_witness, Witness):
        witness = withdrawals_or_witness
    else:
        witness = withdrawals2witness(withdrawals_or_witness)
    assert len(witness.rows) == MAX_WITHDRAWALS

    exception = None
    try:
        verify_circuit(
            witness,
            MAX_WITHDRAWALS,
        )
    except AssertionError as e:
        exception = e
    if success:
        if exception:
            raise exception
        assert exception is None
    else:
        assert exception is not None


# def test_tx2witness():
#     sk = keys.PrivateKey(b"\x01" * 32)
#     pk = sk.public_key
#     addr = pk.to_canonical_address()

#     chain_id = 23

#     nonce = 543
#     gas_price = 1234
#     gas = 987654
#     to = 0x12345678
#     value = 0x1029384756
#     data = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99])

#     tx = Withdrawal(nonce, gas_price, gas, to, value, data, 0, 0, 0)
#     tx = sign_tx(sk, tx, chain_id)
#     keccak_table = KeccakTable()
#     rows, sign_verification = tx2witness(0, tx, chain_id, r, keccak_table)
#     for row in rows:
#         if row.tag == Tag.CallerAddress:
#             assert addr == row.value.value().n.to_bytes(20, "big")


# makes fake mpt updates for a list of rows.
# the withdrawal root is incremented by 5 for each MPT update.
def mock_mpt_update(
    id: U64, validator_id: U64, address: U160, amount: U64, prev_root: int
) -> MPTTableRow:
    encoded_withdrawal = rlp.encode([id, validator_id, address, amount])
    withdrawal_hash = keccak(encoded_withdrawal)
    root = prev_root + 5
    return MPTTableRow(
        FQ(address),
        FQ(MPTProofType.WithdrawalMod),
        Word(id),
        Word(root),
        Word(prev_root),
        Word(withdrawal_hash),
        Word(0),
    )


def gen_withdrawals(num: int) -> Tuple[List[Withdrawal], set[MPTTableRow]]:
    withdrawal_id = U64(randrange(0, 2**64))

    withdrawals = []
    mpt_table = set()
    prev_root:int = 0
    for i in range(num):
        withdrawal_id += i
        validator_id = U64(randrange(0, 2**64))
        address = U160(randrange(1, 2**160))
        amount = U256(randrange(1, 2**256))
        mpt_table_row: MPTTableRow = mock_mpt_update(withdrawal_id, validator_id, address, amount, prev_root)
        withdrawal = Withdrawal(
            withdrawal_id , validator_id, address, amount, mpt_table_row.root.int_value()
        )

        withdrawals.append(withdrawal)
        mpt_table.add(mpt_table_row)
        prev_root = mpt_table_row.root.int_value()
        # print(f"{hex(address), hex(amount)}")

    return withdrawals, mpt_table


def test_verify_withdrawal():
    MAX_WITHDRAWALS = 2

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS)


# def test_bad_address():
#     witness, chain_id, MAX_WITHDRAWALS, MAX_CALLDATA_BYTES = gen_valid_witness()
#     sign_verifications = witness.sign_verifications
#     sign_verifications[0].address = FQ(1234)
#     witness = Witness(witness.rows, witness.keccak_table, sign_verifications)
#     verify(witness, MAX_WITHDRAWALS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


# def test_bad_msg_hash():
#     witness, chain_id, MAX_WITHDRAWALS, MAX_CALLDATA_BYTES = gen_valid_witness()
#     sign_verifications = witness.sign_verifications
#     sign_verifications[0].msg_hash = Word(4567)
#     witness = Witness(witness.rows, witness.keccak_table, sign_verifications)
#     verify(witness, MAX_WITHDRAWALS, MAX_CALLDATA_BYTES, chain_id, r, success=False)


# def test_bad_addr_copy():
#     witness, chain_id, MAX_WITHDRAWALS, MAX_CALLDATA_BYTES = gen_valid_witness()
#     rows = witness.rows
#     row_addr_offset = 0 * Tag.TxSignHash + Tag.CallerAddress - 1
#     rows[row_addr_offset].value = WordOrValue(FQ(1213))
#     witness = Witness(rows, witness.keccak_table, witness.sign_verifications)
#     verify(witness, MAX_WITHDRAWALS, MAX_CALLDATA_BYTES, chain_id, r, success=False)
