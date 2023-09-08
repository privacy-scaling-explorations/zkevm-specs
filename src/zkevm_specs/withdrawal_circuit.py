from typing import NamedTuple, List, Set, Optional, Union, Mapping

from zkevm_specs.evm_circuit.table import MPTProofType, MPTTableRow
from zkevm_specs.util.typing import U256
from .util import (
    FQ,
    Word,
    Expression,
    U160,
    U64,
    is_circuit_code,
)
import rlp  # type: ignore
from .evm_circuit import lookup


class Row:
    """
    Withdrawal circuit row
    """

    withdrawal_id: FQ
    validator_id: FQ
    address: Word
    amount: Word

    # MPT root
    root: Word

    def __init__(
        self, withdrawal_id: FQ, validator_id: FQ, address: Word, amount: Word, root: Word
    ):
        self.withdrawal_id = withdrawal_id
        self.validator_id = validator_id
        self.address = address
        self.amount = amount
        self.root = root


class MPTTable:
    """
    MPTTable used for lookup from the withdrawal circuit.
    """

    table: Set[MPTTableRow]

    def __init__(self, mpt_table: Set[MPTTableRow]):
        self.table = mpt_table

    def mpt_lookup(
        self,
        address: Expression,
        proof_type: Expression,
        storage_key: Word,
        value: Word,
        value_prev: Word,
        root: Word,
        root_prev: Word,
    ) -> MPTTableRow:
        query: Mapping[str, Optional[Union[FQ, Expression, Word]]] = {
            "address": address,
            "proof_type": proof_type,
            "storage_key": storage_key,
            "value": value,
            "value_prev": value_prev,
            "root": root,
            "root_prev": root_prev,
        }
        return lookup(MPTTableRow, self.table, query)


class Witness(NamedTuple):
    rows: List[Row]  # Transaction table rows
    mpt_table: MPTTable


class Withdrawal(NamedTuple):
    """
    Ethereum Withdrawals
    """

    id: U64
    validator_id: U64
    address: Union[None, U160]
    amount: U64

    # MPT root
    root: U256


@is_circuit_code
def verify_circuit(
    witness: Witness,
    MAX_WITHDRAWALS: int,
) -> None:
    """
    Entry level circuit verification function
    """

    rows = witness.rows
    root_prev = Word(0)
    for row_index in range(MAX_WITHDRAWALS):
        assert_msg = f"Constraints failed for withdrawal_index = {row_index}"

        row = rows[row_index]

        # `amount` must not be zero in a normal withdrawal
        is_not_padding = FQ(row.value != 0)

        # Check withdraw id if it's not the last row
        if not row_index == MAX_WITHDRAWALS - 1:
            # `withdrawal_id` must be increased monotonically
            assert rows[row_index + 1].withdrawal_id == row.withdrawal_id + 1, (
                f"{assert_msg}: {rows[row_index + 1].withdrawal_id} != "
                + f"{row.withdrawal_id + 1}"
            )

        # mpt lookup
        encoded_withdrawal_data = rlp.encode(
            [row.withdrawal_id, row.validator_id, row.address, row.amount]
        )
        witness.mpt_table.mpt_lookup(
            row.address,
            is_not_padding * FQ(MPTProofType.NonExistingAccountProof)
            + (1 - is_not_padding) * FQ(MPTProofType.WithdrawalMod),
            row.withdrawal_id,
            encoded_withdrawal_data,
            Word(0),
            row.root,
            root_prev,
        )

        # assign current root as previous one
        root_prev = rows[row_index].root


def padding_withdrawal(withdrawal_id: int, root: U256) -> List[Row]:
    return [Row(FQ(withdrawal_id), FQ(0), Word(0), Word(0), root)]


def tx2witness(withdrawal: Withdrawal) -> Row:
    """
    Generate the witness data for a single withdrawal: generate the withdrawal table rows
    """

    return Row(
        withdrawal.id,
        FQ(withdrawal.validator_id),
        Word(withdrawal.address),
        Word(withdrawal.amount),
        Word(withdrawal.root),
    )


def txs2witness(
    withdrawals: List[Withdrawal], MAX_WITHDRAWALS: int, mpt_table: MPTTable
) -> Witness:
    """
    Generate the complete witness of the withdrawals for a fixed size circuit.
    """

    assert len(withdrawals) <= MAX_WITHDRAWALS

    last_withdrawal_id = 0
    last_root: U256 = 0
    rows: List[Row] = []
    for withdrawal in withdrawals:
        withdrawal_row = tx2witness(withdrawal)

        last_withdrawal_id = withdrawal_row.withdrawal_id
        last_root = withdrawal_row.root
        rows.append(withdrawal_row)

    for i in range(len(withdrawals), MAX_WITHDRAWALS):
        rows.append(padding_withdrawal(last_withdrawal_id + i + 1 - len(withdrawals), last_root))

    return Witness(rows, mpt_table)
