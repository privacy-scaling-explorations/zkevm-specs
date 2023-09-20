from typing import NamedTuple, List, Set, Optional, Union, Mapping, Tuple
from zkevm_specs.evm_circuit.table import MPTProofType, MPTTableRow
from .util import (
    FQ,
    RLC,
    Word,
    Expression,
    is_circuit_code,
)
import rlp  # type: ignore
from .evm_circuit import lookup
from eth_utils import keccak


class Row:
    """
    Withdrawal circuit row
    """

    withdrawal_id: FQ
    validator_id: FQ
    address: FQ
    amount: Word

    # keccak of rlp encoding above fields
    hash: Word

    # MPT root
    root: Word

    def __init__(
        self, withdrawal_id: FQ, validator_id: FQ, address: FQ, amount: Word, hash: Word, root: Word
    ):
        self.withdrawal_id = withdrawal_id
        self.validator_id = validator_id
        self.address = address
        self.amount = amount
        self.hash = hash
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


class KeccakTable:
    # The columns are: (is_enabled, input_rlc, input_len, output)
    table: Set[Tuple[FQ, FQ, FQ, Word]]

    def __init__(self):
        self.table = set()
        self.table.add((FQ(0), FQ(0), FQ(0), Word(0)))  # Add all 0s row

    def add(self, input: bytes, keccak_randomness: FQ):
        output = keccak(input)
        length = len(input)
        self.table.add(
            (
                FQ(1),
                RLC(bytes(reversed(input)), keccak_randomness, n_bytes=length).expr(),
                FQ(length),
                Word(output),
            )
        )

    def lookup(self, is_enabled: FQ, input_rlc: FQ, input_len: FQ, output: Word, assert_msg: str):
        assert (is_enabled, input_rlc, input_len, output) in self.table, (
            f"{assert_msg}: {(is_enabled, input_rlc, input_len, output)} "
            + "not found in the lookup table"
        )


class Witness(NamedTuple):
    rows: List[Row]  # Withdrawal table rows
    mpt_table: MPTTable
    keccak_table: KeccakTable


@is_circuit_code
def verify_circuit(
    witness: Witness,
    MAX_WITHDRAWALS: int,
    keccak_randomness: FQ,
) -> None:
    """
    Entry level circuit verification function
    """

    rows = witness.rows
    root_prev = Word(0)
    keccak_table = witness.keccak_table
    mpt_table = witness.mpt_table

    for row_index in range(MAX_WITHDRAWALS):
        assert_msg = f"Constraints failed for withdrawal_index = {row_index}"

        row = rows[row_index]

        # `amount` must not be zero in a normal withdrawal
        is_not_padding = FQ(row.amount != Word(0))

        # Check withdraw id if it's not the last row
        if not row_index == MAX_WITHDRAWALS - 1:
            # `withdrawal_id` must be increased monotonically
            assert rows[row_index + 1].withdrawal_id == row.withdrawal_id + 1, (
                f"{assert_msg}: {rows[row_index + 1].withdrawal_id} != "
                + f"{row.withdrawal_id + 1}"
            )

        encoded_withdrawal_data = rlp.encode(
            [
                int(row.withdrawal_id),
                int(row.validator_id),
                int(row.address),
                row.amount.int_value(),
            ]
        )

        # keccak_lookup
        withdrawal_hash = row.hash
        length = len(encoded_withdrawal_data)
        keccak_table.lookup(
            is_not_padding,
            is_not_padding
            * RLC(
                bytes(reversed(encoded_withdrawal_data)), keccak_randomness, n_bytes=length
            ).expr(),
            is_not_padding * FQ(length),
            withdrawal_hash.select(is_not_padding),
            assert_msg,
        )

        # mpt lookup
        mpt_table.mpt_lookup(
            row.address,
            is_not_padding * FQ(MPTProofType.WithdrawalMod)
            + (1 - is_not_padding) * FQ(MPTProofType.NonExistingAccountProof),
            Word(row.withdrawal_id.n),
            withdrawal_hash,
            Word(0),
            row.root,
            root_prev,
        )

        # FIXME: convert amount (from 1e9 to 1e18) abd update validator's balance

        # assign current root as previous one
        root_prev = rows[row_index].root
