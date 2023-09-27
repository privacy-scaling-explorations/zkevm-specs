from typing import List, Tuple
import rlp  # type: ignore
from zkevm_specs.withdrawal_circuit import *
from zkevm_specs.util import FQ, U64, U160, U256
from random import randrange
from eth_utils import keccak
from common import rand_fq

r = rand_fq()


class Withdrawal(NamedTuple):
    """
    Ethereum Withdrawals
    """

    id: U64
    validator_id: U64
    address: U160
    amount: U64


def padding_withdrawal(root: U256) -> List[Row]:
    return [Row(FQ(0), FQ(0), FQ(0), FQ(0), Word(0), root)]


def withdrawal2witness(
    withdrawal: Withdrawal,
    keccak_table: KeccakTable,
    keccak_randomness: FQ,
    mpt_table_set: set,
    root: U256,
    prev_root: U256,
) -> Row:
    """
    Generate the witness data for a single withdrawal: generate the withdrawal table rows
    """
    encoded_withdrawal_data = rlp.encode(
        [
            int(withdrawal.id),
            int(withdrawal.validator_id),
            int(withdrawal.address),
            int(withdrawal.amount),
        ]
    )
    keccak_table.add(encoded_withdrawal_data, keccak_randomness)

    mpt_table_row = mock_mpt_update(
        withdrawal.id, withdrawal.validator_id, withdrawal.address, withdrawal.amount, prev_root
    )
    mpt_table_set.add(mpt_table_row)

    return Row(
        FQ(withdrawal.id),
        FQ(withdrawal.validator_id),
        FQ(withdrawal.address),
        FQ(withdrawal.amount),
        Word(bytes(keccak(encoded_withdrawal_data))),
        Word(root),
    )


def withdrawals2witness(
    withdrawals: List[Withdrawal],
    MAX_WITHDRAWALS: int,
    mpt_roots: List[U256],
    keccak_randomness: FQ,
) -> Witness:
    """
    Generate the complete witness of the withdrawals for a fixed size circuit.
    """

    assert len(withdrawals) <= MAX_WITHDRAWALS

    last_root: U256 = 0
    rows: List[Row] = []
    keccak_table = KeccakTable()
    mpt_table_set = set()
    block_table_set = set()

    for withdrawal, root in zip(withdrawals, mpt_roots):
        withdrawal_row = withdrawal2witness(
            withdrawal, keccak_table, keccak_randomness, mpt_table_set, root, last_root
        )

        last_root = root
        rows.append(withdrawal_row)

    for i in range(len(withdrawals), MAX_WITHDRAWALS):
        rows.append(padding_withdrawal(last_root))

    block_table_set.add(BlockTableRow(FQ(BlockContextFieldTag.WithdrawalRoot), FQ(0), Word(last_root)))
    
    return Witness(rows, MPTTable(mpt_table_set), keccak_table, BlockTable(block_table_set))


def verify(
    witness: Witness,
    MAX_WITHDRAWALS: int,
    keccak_randomness: FQ,
    success: bool = True,
):
    """
    Verify the circuit with the assigned witness (or the witness calculated
    from the withdrawals).  If `success` is False, expect the verification to
    fail.
    """
    assert len(witness.rows) == MAX_WITHDRAWALS

    exception = None
    try:
        verify_circuit(witness, MAX_WITHDRAWALS, keccak_randomness)
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


def gen_withdrawals(num: int) -> Tuple[List[Withdrawal], List[U256]]:
    withdrawal_id = U64(randrange(0, 2**64))

    withdrawals = []
    roots = []
    mpt_table = set()
    prev_root: int = 0
    for i in range(num):
        validator_id = U64(randrange(0, 2**64))
        address = U160(randrange(1, 2**160))
        amount = U64(randrange(1, 2**64))
        mpt_table_row: MPTTableRow = mock_mpt_update(
            withdrawal_id + i, validator_id, address, amount, prev_root
        )
        withdrawal = Withdrawal(withdrawal_id + i, validator_id, address, amount)

        withdrawals.append(withdrawal)
        roots.append(mpt_table_row.root.int_value())
        mpt_table.add(mpt_table_row)
        prev_root = mpt_table_row.root.int_value()

    return withdrawals, roots


def test_withdrawal_withdrawals2witness():
    MAX_WITHDRAWALS = 20

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)

    # withdrawals.pop() pops from the last item, so we reverse here.
    withdrawals.reverse()
    for row in witness.rows:
        wd = withdrawals.pop()
        assert wd.id == row.withdrawal_id.n
        assert wd.address == row.address.n


def test_withdrawal_basic():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)
    verify(witness, MAX_WITHDRAWALS, r)


def test_withdrawal_id_not_incremental():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)
    witness.rows[1].withdrawal_id -= 1
    verify(witness, MAX_WITHDRAWALS, r, success=False)


def test_withdrawal_inconsistent_id():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)
    witness.rows[0].withdrawal_id = 999
    verify(witness, MAX_WITHDRAWALS, r, success=False)


def test_withdrawal_inconsistent_validator_id():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)
    witness.rows[0].validator_id = 999
    verify(witness, MAX_WITHDRAWALS, r, success=False)


def test_withdrawal_inconsistent_address():
    MAX_WITHDRAWALS = 5

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)
    witness.rows[0].address = 0xDEADBEEF
    verify(witness, MAX_WITHDRAWALS, r, success=False)


def test_withdrawal_inconsistent_amount():
    MAX_WITHDRAWALS = 2

    withdrawals, mpt_roots = gen_withdrawals(MAX_WITHDRAWALS)
    witness = withdrawals2witness(withdrawals, MAX_WITHDRAWALS, mpt_roots, r)
    witness.rows[0].amount = 10
    verify(witness, MAX_WITHDRAWALS, r, success=False)
