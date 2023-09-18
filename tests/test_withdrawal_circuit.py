from typing import Union, List, Tuple
import rlp  # type: ignore
from zkevm_specs.withdrawal_circuit import *
from zkevm_specs.util import FQ, U64
from random import randrange
from eth_utils import keccak


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
    except Exception as e:
        exception = e
    if success:
        if exception:
            raise exception
        assert exception is None
    else:
        assert exception is not None


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
    prev_root: int = 0
    for i in range(num):
        validator_id = U64(randrange(0, 2**64))
        address = U160(randrange(1, 2**160))
        amount = U256(randrange(1, 2**256))
        mpt_table_row: MPTTableRow = mock_mpt_update(
            withdrawal_id + i, validator_id, address, amount, prev_root
        )
        withdrawal = Withdrawal(
            withdrawal_id + i, validator_id, address, amount, mpt_table_row.root.int_value()
        )

        withdrawals.append(withdrawal)
        mpt_table.add(mpt_table_row)
        prev_root = mpt_table_row.root.int_value()

    return withdrawals, mpt_table


def test_verify_withdrawals2witness():
    MAX_WITHDRAWALS = 20

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))

    # withdrawals.pop() pops from the last item, so we reverse here.
    withdrawals.reverse()
    for row in witness.rows:
        wd = withdrawals.pop()
        assert wd.id == row.withdrawal_id.n
        assert wd.address == row.address.n


def test_verify_withdrawal():
    MAX_WITHDRAWALS = 20

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS)


def test_id_not_incremental():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    row = witness.rows[1]
    row.withdrawal_id = witness.rows[0].withdrawal_id
    witness = Witness(witness.rows, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS, success=False)


def test_inconsistent_id():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    row = witness.rows[0]
    row.withdrawal_id = 999
    witness = Witness(witness.rows, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS, success=False)


def test_inconsistent_validator_id():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    row = witness.rows[0]
    row.validator_id = 999
    witness = Witness(witness.rows, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS, success=False)


def test_inconsistent_address():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    row = witness.rows[0]
    row.address = 0xDEADBEEF
    witness = Witness(witness.rows, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS, success=False)


def test_inconsistent_amount():
    MAX_WITHDRAWALS = 2

    withdrawals, mpt_table = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, MPTTable(mpt_table))
    row = witness.rows[0]
    row.amount = 10
    witness = Witness(witness.rows, MPTTable(mpt_table))
    verify(witness, MAX_WITHDRAWALS, success=False)
